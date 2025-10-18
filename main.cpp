#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <list>
#include <map>
#include <mutex>
#include <sstream>
#include <thread>
#include <unordered_map>
#include <unordered_set>

#include <arpa/inet.h>
#include <ctype.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <termios.h>
#include <unistd.h>

#include <curses.h>

#include "civetweb.h"

#define HTML "View.html"
#define JS "View.js"

#define DEBUG 0
#if DEBUG
#define LOG(...) fprintf(stderr, __VA_ARGS__)
#define LOG_FUNCTION do { LOG("%s(), state = %d\r\n", __func__, m_mame_connection_state); } while(0)
#define L(...) do { __VA_ARGS__; }while(0)
#if DEBUG > 1
#define LOGD(...) fprintf(stderr, __VA_ARGS__)
#endif
#else // DEBUG
#define LOG(...) do{}while(0)
#define LOG_FUNCTION do{}while(0)
#define L(...) do{}while(0)
#endif // DEBUG
#ifndef LOGD
#define LOGD(...) do{}while(0)
#endif

#if USE_SSL
#include <openssl/ssl3.h>

static const unsigned char ssl_key[] {
#embed SSL_KEY
};

static const unsigned char ssl_cert[] {
#embed SSL_CERT
};

#endif // USE_SSL

static const char html[] {
#embed HTML
};
static std::string htmls(html);

static const char js[] {
#embed JS
};
static std::string jss(js);

static const char WS_URL[] = "/socket";

static int connection_counter = 0;

struct Pipe {
  int r;
  int w;
  Pipe() {
    int pfds[2];
    if (pipe(pfds) == 0) {
      r = pfds[0];
      w = pfds[1];
      fcntl(r, F_SETFL, O_NONBLOCK);
    } else {
      r = w = -1;
    }
  }
  operator bool() {
    return r >= 0 && w >= 0;
  }
  void checkRead(pollfd &pfd) {
    pfd.fd = r;
    pfd.events = POLLIN | POLLERR;
  }
  int write(const void *s, size_t n) {
    return ::write(w, s, n);
  }
  int write(char c) {
    return write(&c, 1);
  }
  int read(void *s, size_t n) {
    return ::read(r, s, n);
  }
  int read(char &c) {
    return read(&c, 1);
  }
};

template<size_t size>
struct MessageCollector {
  std::array<char, size> m_buffer;
  size_t m_received = 0;
  size_t m_message_length = 0;
  bool m_overflow = false;

  void handle(char c) {
    // LOG("Received %02x, overflow=%d\r\n", c, m_overflow);
    if (m_overflow) {
      if (c == '\n') {
        // LOG("Found end of overflowing message, restarting.\r\n");
        m_received = 0;
        m_overflow = false;
      } else {
        // LOG("In buffer overflow, ignoring.\r\n");
      }
    } else {
      switch(c) {
        case '\r': // ignore
          // LOG("ignoring CR\r\n");
          break;

        case '\n':
          // LOG("LF, have a message of %ld bytes\r\n", m_received);
          m_message_length = m_received;
          m_received = 0;
          break;

        default:
          if (m_received >= m_buffer.size()) {
            // LOG("Already have %ld of %ld characters - buffer overflow!\r\n", m_received, m_buffer.size());
            m_overflow = true;
            m_message_length = 0;
            m_received = 0;
          } else {
            m_message_length = 0;
            m_buffer[m_received++] = c;
            // LOG("accumulated character %02x, now have %ld (of max %ld)\r\n", c, m_received, m_buffer.size());
          }
      }
    }
  }

  bool has_message() { return m_message_length > 0; }

  std::string copy_message() {
    std::stringstream os;
    os.write(&m_buffer[0], m_message_length);
    return os.str();
  }

  const char *message_data() { return (const char *)&m_buffer[0]; }
  size_t message_length() { return m_message_length; }

  void clear_message() {
    m_message_length = m_received = 0;
    m_overflow = false;
  }
};

enum connection_state {
  cs_idle = 0,
  cs_starting,
  cs_connecting,
  cs_reconnecting,
  cs_connected,
  cs_stopping,
};

struct Connected {
  bool is_client = false;
  Connected(bool is_client) : is_client(is_client) {}
};

struct WSClient : public Connected {
  struct mg_connection *m_connection;
  int m_connection_number;
  bool m_ready = false;

  WSClient() : Connected(true) {}

  void sendConnectionState(int cs) {
    LOG("Sending connection state %d:", cs);
    if (cs == cs_connecting) {
      LOG("connecting\r\n");
      send("MConnecting to MAME ...");
    } else if (cs == cs_reconnecting) {
      LOG("reconnecting\r\n");
      send("MReconnecting to MAME ...");
    } else {
      LOG("other, no message\r\n");
      send("M");
    }
  }

  void send(const char *data, size_t len) {
    if (m_connection && m_ready) {
      mg_websocket_write(m_connection, MG_WEBSOCKET_OPCODE_TEXT, data, len);
    }
  }

  void send(const std::string &message) {
    L(L(std::cerr << std::format("Sending '{}' to client {}", message, m_connection_number) << std::endl));
    send(message.data(), message.length());
  }
};

std::ostream &operator<<(std::ostream &o, const struct addrinfo *pai) {
  if (pai->ai_family == AF_INET) {
    struct sockaddr_in *psai = (struct sockaddr_in*)pai->ai_addr;
    char ip[INET_ADDRSTRLEN];
    if (inet_ntop(pai->ai_family, &(psai->sin_addr), ip, INET_ADDRSTRLEN) != NULL) {
      return o << std::format("{:s}:{:d}", ip, ntohs(psai->sin_port));
    } else {
      return o << "[Unable to print IPv4 address: " << strerror(errno) << "]";
    }
  } else if (pai->ai_family == AF_INET6) {
    struct sockaddr_in6 *psai = (struct sockaddr_in6*)pai->ai_addr;
    char ip[INET6_ADDRSTRLEN];
    if (inet_ntop(pai->ai_family, &(psai->sin6_addr), ip, INET6_ADDRSTRLEN) != NULL) {
      return o << std::format("[{:s}]:{:d}", ip, ntohs(psai->sin6_port));
    } else {
      return o << "[Unable to print IPv6 address: " << strerror(errno) << "]";
    }
  } else {
    return o << std::format("Don't know how to convert family {:d} addresses\r\n", pai->ai_family);
  }
}

std::ostream &operator<<(std::ostream &o, const struct addrinfo &ai) {
  return o << &ai;
}

struct BlinkTimer {
  std::atomic<bool> exit_thread { false };
  std::condition_variable cv;
  std::mutex m;
  int phase = 0;
  std::function<void(int)> blink_phase;
  std::thread thread;

  BlinkTimer(std::function<void(int)> blink_phase)
  : blink_phase(blink_phase)
  {
    thread = std::thread([this] { this->run(); });
  }

  ~BlinkTimer() {
    {
      std::lock_guard<std::mutex> guard(m);
      exit_thread = true;
    }
    cv.notify_all();
    thread.join();
  }

  void run() {
    auto next = std::chrono::steady_clock::now() + std::chrono::milliseconds(250);
    while (true) {
      {
        std::unique_lock<std::mutex> lock(m);
        auto status = cv.wait_until(lock, next);
        if (exit_thread) return;

        if (status == std::cv_status::timeout) {
          phase = (phase + 1) & 3;
          blink_phase(phase);
        }

        auto now = std::chrono::steady_clock::now();
        while (next < now)
          next += std::chrono::milliseconds(250);
      }
    }
  }
};

struct Display {
  std::function<void(const std::string&)> send;

  static constexpr uint8_t ATTR_NORMAL    = 0x00;
	static constexpr uint8_t ATTR_UNDERLINE = 0x01;
	static constexpr uint8_t ATTR_BLINK     = 0x02;

  static constexpr uint8_t LIGHT_OFF   = 0x00;
  static constexpr uint8_t LIGHT_ON    = 0x02;
  static constexpr uint8_t LIGHT_BLINK = 0x03;

  int row = 0, col = 0, attr = 0, saved_row = 0, saved_col = 0;
  bool calib = false, light = false;

  char chars[2][40] { 0 };
  uint8_t attrs[2][40] { ATTR_NORMAL };
  int light_states[0x40] { LIGHT_OFF };

  Display(std::function<void(const std::string&)> send) : send(send) {}

  void clear_screen() {
    std::fill(&chars[0][0], &chars[1][40], 0);
    std::fill(&attrs[0][0], &attrs[1][40], ATTR_NORMAL);
    col = row = 0;
    attr = 0;
    send("DX");
  }

  void send_contents() {
    send("DX");
    for (int i = 0; i < 0x40; i++) {
      send(std::format("L {:d} {:d}", i, light_states[i]));
    }
    std::ostringstream ss;
    ss << "D C 0 0";
    for (int row = 0; row < 2; row++) {
      for (int col = 0; col < 40; col++) {
        ss << std::format(" {:02x} {:x}", chars[row][col], attrs[row][col]);
      }
    }
    std::string s(ss.str());
    LOG("Display.send_contents(): '%s'\n", s.c_str());
    send(s);
  }

  void move_right() {
    col++;
    if (39 < col) {
      col -= 40;
      row++;
      if (2 < row) {
        row = row - 2;
      }
    }
  }

  void move_left() {
    col--;
    if (col < 0) {
      col = col + 40;
      row--;
      if (row < 0) {
        row += 2;
      }
    }
  }

  void handle_display_char(uint8_t c) {
    if (0x20 <= c && c < 0x7f)
      LOGD("HDC %02x '%c': ", c, c);
    else
      LOGD("HDC %02x    : ", c);

    if (calib) {
      LOGD("skipping next byte after calibration\r\n");
      calib = false;
    } else if (light) {
      int light_number = c & 0x3f;

      auto light_state = (c & 0xc0) >> 6;
      light_states[light_number] = light_state;

      LOGD(" - %d %d\r\n", light_number, light_state);
      send(std::format("L {:d} {:d}", light_number, light_state));
      light = false;
    } else if ((0x80 <= c) && (c < 0xd0)) {
      // move cursor to position
      row = ((c & 0x7f) >= 40) ? 1 : 0;
      col = (c & 0x7f) % 40;
      attr = attrs[row][col];
      LOGD("%02x: -> (%d, %d)\r\n", c, row, col);
    } else if (0xd0 <= c) {
      // single-byte commands
      switch (c) {
        case 0xd0:  // blink start
          LOGD("d1: blink\r\n");
          attr |= ATTR_BLINK;
          break;

        case 0xd1:  // cancel all attributes
          LOGD("d1: cancel attributes\r\n");
          attr = 0;
          break;

        case 0xd2:  // blinking underline
          LOGD("d2: blinking underline\r\n");
          attr |= ATTR_BLINK | ATTR_UNDERLINE;
          break;

        case 0xd3:  // underline
          LOGD("d3: underline\r\n");
          attr |= ATTR_UNDERLINE;
          break;

        case 0xd4:  // move curser one step right
          LOGD("d4: right %d", col);
          move_right();
          LOGD(" -> %d\r\n", col);
          break;

          case 0xd5:  // move curser one step left
          LOGD("d5: left  %d", col);
          move_left();
          LOGD(" -> %d\r\n", col);
          break;

        case 0xd6:  // clear screen
          LOGD("d6: clear screen\r\n");
          clear_screen();
          break;

        case 0xf5:  // save cursor position
          LOGD("f5: save pos (%d, %d)\r\n", row, col);
          saved_col = col;
          saved_row = row;
          break;

        case 0xf6:  // restore cursor position
          LOGD("f6: restore pos (%d, %d)", row, col);
          col = saved_col;
          row = saved_row;
          LOGD(" -> (%d, %d)\r\n", row, col);
          attr = attrs[row][col];
          break;

        case 0xfb: // request calibration
          LOGD("0xff: calibration\r");
          calib = true;
          break;

        case 0xfd: // also clear screen?
          LOGD("fd: clear screen\r\n");
          clear_screen();
          break;

        case 0xff:
          LOGD("0xff: light\r\n");
          // button light state command
          light = true;
          break;

        default:
          char cx = chars[row][col];
          LOGD("Unknown control code %02x (@ %d, %d, %02x '%c')\r\n", c, row, col, cx, cx);
          break;
      }
    } else if ((0x20 <= c) && (c < 0x7f)) {
      // a character to display
      LOGD("[char %02x]\r\n", c);
      chars[row][col] = c;
      attrs[row][col] = attr;

      send(std::format("DC {:d} {:d} {:02x} {:1x}", row, col, c, attr));

      move_right();
    } else if (c == 0x7f) {
      // DEL character -> move one step right? Nope - cursor just moves past column 39,
      // perhaps onto column 0 on the next row!
      LOGD("7f: Unknown function\r\n");
    } else {
      char c = chars[row][col];
      LOGD("Unknown character code %02x (@ %d, %d, %02x '%c')\r\n", c, row, row, c, c);
    }
  }
};

static int mame_websocket_data_handler(struct mg_connection *conn,
    int flags,
    char *data,
    size_t data_len,
    void *user_data);

static void mame_websocket_close_handler(const struct mg_connection *conn,
    void *user_data);

struct Server : Connected {
  std::string m_mame_direct;
  std::string m_mame_ws;

  std::filesystem::path m_webroot;

  // Also used for locking.
  struct mg_context *m_mg_ctx = nullptr;

  mg_connection *m_mame_conn = nullptr;
  int m_mame_socket = -1;
  bool m_websocket = false;
  int m_mame_connection_state = cs_idle;

  std::unordered_set<WSClient *> m_ws_clients;
  std::map<std::string, std::string> m_template_values;

  std::thread m_mame_thread;
  Pipe m_mame_thread_commands;

  std::function<void(char)> handle_websocket_display_char;
  std::function<void(void)> handle_send_contents;

  void handle_server_info(const std::string_view &message) {
    // try to parse this as server info
    // std::cerr << std::format("Maybe Server info: '{}' ({})\r\n", message, message.size());
    auto b = message.begin();
    auto i = message.find("I");
    if (i == 0) {
      auto kbs = message.find_first_not_of(" \r\n\t", 1);
      if (kbs != std::string::npos) {
        auto comma = message.find(',', kbs);
        if (comma != std::string::npos) {
          auto keyboard = message.substr(kbs, comma - kbs);
          auto version = message.substr(comma + 1);

          // std::cerr << std::format("Have Server info! keyboard '{}' ({}), version '{}' ({})\r\n",
          //   keyboard, keyboard.size(), version, version.size());
          set_template_value("keyboard", keyboard);
          set_template_value("version", version);
        }
      }
    }
  }

  int mame_websocket_data(int flags, char *data, size_t data_len) {
    // LOG("websocket data: %d '%s'\r\n", (int)data_len, std::string(std::string_view(data, data_len)).c_str());
    if (data_len >= 2) {
      switch(data[0]) {
        case 'D': // a character for the display processor
          if (handle_websocket_display_char) {
            for (int i = 1; i < data_len; i++) {
              handle_websocket_display_char(data[i]);
            }
          }
          break;

        case 'A': // an Analog value;
          L(std::cerr << "Ignoring Analog '" << std::string_view(data, data_len) << "'" << std::endl);
          break;

        case 'B': // a Button is being pressed or released
          L(std::cerr << "Ignoring Button '" << std::string_view(data, data_len) << "'" << std::endl);
          break;

        case 'I': // server Information
          handle_server_info(std::string_view(data, data_len));
          send_to_all_clients(data, data_len);
          break;

        default:
          L(std::cerr << "Ignoring Unknown message '" << std::string_view(data, data_len) << "'" << std::endl);
      }
    }
    return 1;
  }

  void mame_websocket_closed(const struct mg_connection *conn) {
    lock();
    if (conn == m_mame_conn) {
      reset_mame_connection();
      m_mame_thread_commands.write('C');
    }
    unlock();
  }

  Server(const std::string &mame_direct, const std::string &mame_ws, const std::string &webroot)
  : Connected(false), m_mame_direct(mame_direct), m_mame_ws(mame_ws), m_webroot(webroot), m_mame_thread_commands() {
    if ((m_mame_thread_commands.r < 0) || (m_mame_thread_commands.w < 0)) {
      L(std::cerr << "!!! Failed to create pipe !!!" << std::endl);
      exit(1);
    }
  }

  void lock() {
    mg_lock_context(m_mg_ctx);
  }

  void unlock() {
    mg_unlock_context(m_mg_ctx);
  }

  void send_to_all_clients(const char *data, size_t len, struct mg_connection *except = nullptr) {
    lock();
    // LOG_FUNCTION;
    // if (data[0] != 'P') {
    //   L(std::cerr << "send_to_all_clients('" << std::string_view(data, len) << "')" << std::endl);
    // }

    for (const auto &c: m_ws_clients) {
      if (c->m_connection != except) c->send(data, len);
    }
    unlock();
  }

  void send_to_all_clients(const std::string &s, struct mg_connection *except = nullptr) {
    send_to_all_clients(s.c_str(), s.size(), except);
  }
  
  void send_contents() {
    LOG("send_contents()\n");
    if (handle_send_contents) {
      LOG("- calling handle_send_contents()\n");
      handle_send_contents();
    } else {
      LOG("- handle_send_contents is null\n");
    }
  }

  void send_to_mame(const char *data, size_t len) {
    lock();
    LOG_FUNCTION;
    if (m_mame_connection_state != cs_connected) {
      LOG("Not connected to MAME, not sending %d '%s'.\r\n", (int)len, std::string(std::string_view(data, (int)len)).c_str());
      return;
    }
    if (m_mame_conn) {
      LOG("Sending %d '%s' to MAME websocket\r\n", (int)len, std::string(std::string_view(data, (int)len)).c_str());
        mg_websocket_client_write(m_mame_conn, MG_WEBSOCKET_OPCODE_BINARY, data, len);
    } else if (m_mame_socket >= 0) {
      // LOG("Sending %d to MAME TCP socket\r\n", len);
      write(m_mame_socket, data, len);
      write(m_mame_socket, "\r\n", 2);
    } else {
      // LOG("No MAME socket, Sending %d to MAME\r\n", len);
    }
    unlock();
  }

  void send_to_mame(const std::string &s) {
    send_to_mame(s.c_str(), s.size());
  }

  void set_mame_connection(mg_connection *conn, int s) {
    lock();
    LOG_FUNCTION;
    if (conn != nullptr && s >= 0) {
      L(std::cerr << "ERROR: Trying to use both TCP and Web socket connections to MAME at the same time! Ignoring" << std::endl);
    } else {
      m_mame_socket = s;
      m_mame_conn = conn;
    }
    unlock();
  }

  void reset_mame_connection() {
    lock();
    LOG_FUNCTION;
    m_mame_conn = nullptr;
    m_mame_socket = -1;
    unlock();
  }

  void add_client(WSClient *client) {
    lock();
    LOG_FUNCTION;

    if (m_ws_clients.empty()) {
      start_talking_to_mame();
    }

    m_ws_clients.insert(client);

    unlock();
  }

  void client_ready(WSClient *client) {
    lock();
    LOG_FUNCTION;
    client->sendConnectionState(m_mame_connection_state);
    unlock();
  }

  void remove_client(WSClient *client) {
    lock();
    LOG_FUNCTION;

    m_ws_clients.erase(client);

    if (m_ws_clients.empty()) {
      stop_talking_to_mame();
    }

    unlock();
  }

  void set_template_value(std::string &key, std::string_view &value) {
    m_template_values.insert_or_assign(key, std::string(value));
  }

  void set_template_value(std::string key, std::string_view value) {
    m_template_values.insert_or_assign(key, std::string(value));
  }

  void clear_template_value(std::string &key) {
    m_template_values.erase(key);
  }

  std::string_view substitute(const std::string &arg) {
    auto i = m_template_values.find(arg);
    if (i != m_template_values.end()) {
      return std::string_view(i->second);
    } else {
      return std::string_view(arg);
    }
  }

  void set_mame_connection_state(int cs) {
    lock();
    LOG("set_mame_connection_state(): %d -> %d\r\n", m_mame_connection_state, cs);
    if (cs != m_mame_connection_state) {
      // LOG("  new state = %d\r\n", cs);
      m_mame_connection_state = cs;
      for (const auto &c: m_ws_clients) {
        c->sendConnectionState(cs);
      }
    }
    unlock();
  }

  void start_talking_to_mame() {
    lock();
    LOG_FUNCTION;
    if (m_mame_connection_state == cs_idle || m_mame_connection_state == cs_stopping) {
      L(std::cerr << "Starting MAME connection thread" << std::endl);
      set_mame_connection_state(cs_starting);
      m_mame_thread = std::thread(&Server::talk_to_mame, this);
    }
    unlock();
  }

  void stop_talking_to_mame() {
    lock();
    LOG_FUNCTION;
    if (m_mame_thread.joinable()) {
      std::thread closing = std::move(m_mame_thread);
      if (m_mame_thread.joinable()) fprintf(stderr, "!!! Still joinable after moving\r\n");
      m_mame_thread_commands.write('Q');
      closing.join();
      if (m_mame_connection_state == cs_stopping) {
        set_mame_connection_state(cs_idle);
      } else {
        fprintf(stderr, "stop_talking_to_mame(): Expected to be in state %d, was in state %d\r\n", cs_stopping, m_mame_connection_state);
      }
    }
    unlock();
  }

  void finish_talking_to_mame() {
    lock();
    LOG_FUNCTION;
    set_mame_connection_state(cs_stopping);
    if (m_mame_conn) {
      mg_websocket_client_write(m_mame_conn, MG_WEBSOCKET_OPCODE_CONNECTION_CLOSE, nullptr, 0);
      mg_set_user_connection_data(m_mame_conn, nullptr);
      // mg_close_connection(m_mame_conn);
      // this may take some time to take hold; the closed callback will be asynchronously.
    }
    if (m_mame_socket >= 0) {
      close(m_mame_socket);
    }
    reset_mame_connection();
    unlock();

    char c;
    // Chear the mame thread command pipe.
    LOG("- Clearing the mame command pipe\r\n");
    while (m_mame_thread_commands.read(c) > 0) { /* no-op */ }
    LOG("- Finished reading from mame command pipe\r\n");
    return;
  }

  void talk_to_mame() {
    LOG_FUNCTION;
    set_mame_connection_state(cs_connecting);

    std::array<char, 1024> error_buffer;

    // Tis lets us poll the command pipe
    struct pollfd pfd;
    m_mame_thread_commands.checkRead(pfd);

    L(std::cerr << "Connecting to MAME ..." << std::endl);

    while (true) {
      mg_connection *conn = nullptr;
      int sfd = -1;

      if (!m_mame_direct.empty()) {
        // Try to connect to the TCP server
        std::cerr << "Trying to connect to " << m_mame_direct << " ...";

        std::string host = m_mame_direct;
        std::string port = "15112";

        auto colon = m_mame_direct.find(':');
        if (colon != std::string::npos) {
          host = m_mame_direct.substr(0, colon);
          port = m_mame_direct.substr(colon+1);
        }

        struct addrinfo hints {0};
        struct addrinfo *result, *rp;
        hints.ai_family = AF_UNSPEC;     /* Allow IPv4 or IPv6 */
        hints.ai_socktype = SOCK_STREAM; /* Stream socket */
        hints.ai_flags = 0;
        hints.ai_protocol = 0;           /* Any protocol */

        int ar = getaddrinfo(host.c_str(), port.c_str(), &hints, &result);

        struct pollfd pfds[2] {0};
        m_mame_thread_commands.checkRead(pfds[0]);

        for (rp = result; rp != NULL; rp = rp->ai_next) {
          sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
          if (sfd == -1) {
            L(std::cerr << "Failed to create socket, trying next one" << std::endl);
            continue;
          }

          // fcntl(sfd, F_SETFL, O_NONBLOCK);

          std::cerr << "Trying to connect to " << rp << " ...";

          connect(sfd, rp->ai_addr, rp->ai_addrlen);

          pfds[1].fd = sfd;
          pfds[1].events = POLLOUT;

          if (poll(pfds, 2, 1000) > 0) {
            if (pfds[0].revents & POLLIN) {
              return finish_talking_to_mame();
            } else if (pfds[1].revents == POLLOUT) {
              L(std::cerr << " Connected!" << std::endl);
              break;                  /* Success */
            }
          }

          L(std::cerr << " Connection failed." << std::endl);
          close(sfd);
          sfd = -1;
        }

        freeaddrinfo(result);           /* No longer needed */
      }

      if (sfd < 0 && !m_mame_ws.empty()) {
        std::string host = m_mame_ws;
        int port = 8080;
        std::string path = "/esqpanel/socket";

        auto colon = m_mame_ws.find(':');
        auto slash = m_mame_ws.find('/');
        if (colon != std::string::npos) {
          host = m_mame_ws.substr(0, colon);
          if (slash != std::string::npos) {
            port = std::stoi(m_mame_ws.substr(colon+1, slash));
            path = m_mame_ws.substr(slash); // the slash is included in the path
          } else {
            port = std::stoi(m_mame_ws.substr(colon+1));
          }
        } else if (slash != std::string::npos) {
          host = m_mame_ws.substr(0, colon);
          path = m_mame_ws.substr(slash+1);
        }

        std::cerr << "Trying to connect to websocket " << m_mame_ws << " ...";

        conn = mg_connect_websocket_client(host.c_str(), port, false,
            &error_buffer[0], error_buffer.size(),
            path.c_str(), /*origin=*/host.c_str(),
            mame_websocket_data_handler,
            mame_websocket_close_handler,
            this);

        if (conn != nullptr) {
          mg_set_user_connection_data(conn, this);
        } else {
          L(std::cerr << "websocket connection failed: '" << std::string_view(&error_buffer[0]) << ";" << std::endl);
        }
      }

      if (sfd < 0 && conn == nullptr) {               /* No address succeeded */
        LOG("No connection succeeded, waiting to retry\r\n");
        // Wait for up to 1 second - but instead of sleep(), we poll the shutdown pipe.
        if (poll(&pfd, 1, 1000) > 0) {
          return finish_talking_to_mame();
        }
        continue;
      }

      // Connected!

      set_mame_connection_state(cs_connected);
      send_to_all_clients("DX"); // clear the clients' screen(s)

      MessageCollector<4096> collector;

      // We are now ready to serve back and forth between MAME and our client(s).
      set_mame_connection(conn, sfd);

      // Send a couple of empty messages
      send_to_mame("");
      send_to_mame("");
      // Request the system information
      send_to_mame("I");
      // And request that MAME send us all the different kinds of data
      send_to_mame("CA0B0D0L0");
      send_to_mame("CA1B1D1L1");

      while (true) {
        if (sfd >= 0) {
          char c;
          int nfds;

          int nread = read_from_mame(c);
          if (nread == 1) {
            collector.handle(c);
            if (collector.has_message() && collector.message_length() > 0) {
              std::string_view message(collector.message_data(), collector.message_length());
              char c = message[0];
              if (c == 'I') {
                handle_server_info(message);
              }

              send_to_all_clients(collector.message_data(), collector.message_length());
              collector.clear_message();
            }
          } else if (nread == 2) {
            LOG("talk_to_mame(): Exiting MAME thread!");
            return finish_talking_to_mame();
          } else {
            L(std::cerr << std::format("Failed to read from MAME!") << std::endl);
            // Exit from the while(true) loop and try to reconnect.
            break;
          }
        } else if (conn != nullptr) {
          Display display([this](const std::string &s) { send_to_all_clients(s); });
          BlinkTimer blink([this](int phase) { send_to_all_clients(std::format("P {:d}", phase)); });

          struct Guard {
            Server &s;
            Guard(Server &s, Display &d) : s(s) {
              s.handle_websocket_display_char = [&d](char c) { d.handle_display_char(c); };
              s.handle_send_contents = [&d]() { d.send_contents(); };
            }
            ~Guard() {
              s.handle_websocket_display_char = nullptr;
              s.handle_send_contents = nullptr;
            }
          } guard(*this, display);

          // Wait until the websocket connection closes, or we're asked to shut down
          if (poll(&pfd, 1, 1000 * 1000) > 0) {
            char cmd;
            if (m_mame_thread_commands.read(cmd) == 1) {
              if (cmd == 'Q') {
                // Quit
                LOG("talk_to_mame(): Exiting MAME thread!");
                return finish_talking_to_mame();
              } else if (cmd == 'C') {
                // Websocket connection was closed
                LOG("talk_to_mame(): Websocket connection closed!");
                // Exit from the while(true) loop and try to reconnect.
                break;
              }
            } else {
              // there was an error reading the command, treat it as a QUIT command
              L(std::cerr << "Error reading command! quitting." << std::endl);
              return finish_talking_to_mame();
            }
          }
        } else {
          // No connection!? should never happen!
          LOG("talk_to_mame(): No connection!");
          // Exit from the while(true) loop.
          break;
        }
      }

      // When we get here, whatever connection _was_ active, no longer is.
      reset_mame_connection();

      set_mame_connection_state(cs_reconnecting);
    }
  }

  bool keepalive(int sfd) {
    int written = write(sfd, "\r\n", 2);
    if (written != 2) {
      L(std::cerr << std::format("Keepalive write failed: {}", strerror(errno)) << std::endl);
      fflush(stdout);
      return false;
    } else {
      // LOG("(K)");
      fflush(stdout);
      return true;
    }
  }

  int read_from_mame(char &c) {
    int nfds;

    struct pollfd pfds[2] {0};
    m_mame_thread_commands.checkRead(pfds[0]);
    pfds[1].fd = m_mame_socket;
    pfds[1].events = POLLIN | POLLHUP;

    while (true) {
      // LOG("p"); fflush(stdout);
      if ((nfds = poll(pfds, 2, 100 * 1000)) >= 0) {
        // LOG("%d", nfds); fflush(stdout);
        if (nfds == 0) {
          // timeout
          if (!keepalive(m_mame_socket)) {
            return 0;
          }
        } else if (pfds[0].revents & POLLIN) {
          LOG("read_from_mame(): Exiting MAME thread!");
          return 2;
        } else if (pfds[1].revents & POLLERR) {
          L(std::cerr << "Error polling MAME" << std::endl);
          return 0;
        } else if (pfds[1].revents & POLLHUP) {
          L(std::cerr << "Hangup polling MAME" << std::endl);
          return 0;
        } else if (pfds[1].revents & POLLIN) {
          int nread = read(m_mame_socket, &c, 1);
          return nread;
        } else {
          L(std::cerr << "Unexpected result polling MAME" << std::endl);
          return 0;
        }
      } else {
        L(std::cerr << "Failed to poll MAME" << std::endl);
        return 0;
      }
    }
  }

  std::filesystem::path html_path() {
    auto path = m_webroot;
    path.append(HTML);
    return path;
  }

  std::filesystem::path js_path() {
    auto path = m_webroot;
    path.append(JS);
    return path;
  }

  std::string load(const std::filesystem::path &path) {
    auto size = std::filesystem::file_size(path);
    std::string s(size, '\0');
    std::ifstream in(path);
    in.read(&s[0], size);
    return s;
  }

  std::string js() {
    if (m_webroot != "") {
      LOG("fetching JS from '%s'\n", js_path().c_str());
      return load(js_path());
    } else {
      return jss;
    }
  }

  std::string html() {
    if (m_webroot != "") {
      LOG("fetching HTML from '%s'\n", html_path().c_str());
      return load(html_path());
    } else {
      return htmls;
    }
  }
};

/**
 * Substitutes one string with another, and returns whether the substitution should be performed.
 * Used when evaluating a template.
 */
typedef std::function<std::string_view(std::string &)> substitution;

void write_template(std::ostream &dst, std::istream &src, substitution substitute, char init, char term) {
  while (src.good()) {
    std::string s;
    getline(src, s, init);
    dst << s;
    if (src.good()) {
      // LOG("template: found initiator '%c'\r\n", init);
      getline(src, s, term);
      if (src.good()) {
        dst << substitute(s);
      } else {
        // LOG("template: reached end before terminator\r\n");
        dst << init;
        dst << s;
      }
    } else {
      // LOG("template: reached end before initiator\r\n");
    }
  }
}

void write_template(std::ostream &dst, const std::string &src, substitution substitute, char init, char term) {
  std::stringstream src_stream(src);
  write_template(dst, src_stream, substitute, init, term);
}

void write_template(std::ostream &dst, const char *src, substitution substitute, char init, char term) {
  std::stringstream src_stream(src);
  write_template(dst, src_stream, substitute, init, term);
}

#if USE_SSL

static int init_ssl(void *ssl_ctx, void *user_data) {
	SSL_CTX *ctx = (SSL_CTX *)ssl_ctx;

	SSL_CTX_use_certificate_ASN1(ctx, sizeof(ssl_cert), ssl_cert);
	SSL_CTX_use_PrivateKey_ASN1(EVP_PKEY_RSA,
	                            ctx,
	                            ssl_key,
	                            sizeof(ssl_key));

	if (SSL_CTX_check_private_key(ctx) == 0) {
		printf("SSL data inconsistency detected\r\n");
		return -1;
	}

	return 0; /* let CivetWeb set up the rest of OpenSSL */
}

#endif // USE_SSL

static int mame_websocket_data_handler(struct mg_connection *conn,
    int flags,
    char *data,
    size_t data_len,
    void *user_data) {
  // L(std::cerr << "mame_websocket_data_handler(" << data_len <<  " bytes)" << std::endl);
  if (user_data) {
    Server *server = static_cast<Server *>(user_data);
    server->mame_websocket_data(flags, data, data_len);
    return 1;
  } else {
    return 0;
  }
}

static void mame_websocket_close_handler(const struct mg_connection *conn,
    void *user_data) {
  L(std::cerr << "mame_websocket_close_handler()" << std::endl);

  if (user_data) {
    Server *server = static_cast<Server *>(user_data);
    server->mame_websocket_closed(conn);
  }
}

/* Handler for new websocket connections. */
static int ws_connect_handler(const struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  /* Allocate data for websocket client context, and initialize context. */

  WSClient *client = new WSClient();
  if (!client) {
    /* reject client */
    return 1;
  }
  client->m_connection_number = __sync_add_and_fetch(&connection_counter, 1);
  mg_set_user_connection_data(conn, client); /* client context assigned to connection */

  server->add_client(client);

  /* DEBUG: New client connected (but not ready to receive data yet). */
  const struct mg_request_info *ri = mg_get_request_info(conn);
  // LOG("Client %u connected\r\n", client->m_connection_number);

  return 0;
}

/* Handler indicating the client is ready to receive data. */
static void ws_ready_handler(struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  /* Get websocket client context information. */
  WSClient *client = static_cast<WSClient *>(mg_get_user_connection_data(conn));
  client->m_connection = conn;
  client->m_ready = true;

  server->client_ready(client);

  const struct mg_request_info *ri = mg_get_request_info(conn);
  (void)ri; /* in this example, we do not need the request_info */

  /* DEBUG: New client ready to receive data. */
  // LOG("Client %u ready to receive data\r\n", client->m_connection_number);
}

/* Handler indicating the client sent data to the server. */
static int ws_data_handler(struct mg_connection *conn,
                int opcode,
                char *data,
                size_t datasize,
                void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  /* Get websocket client context information. */
  WSClient *client = static_cast<WSClient *>(mg_get_user_connection_data(conn));
  const struct mg_request_info *ri = mg_get_request_info(conn);
  (void)ri; /* in this example, we do not need the request_info */

  /* DEBUG: Print data received from client. */
  const char *messageType = "unknown";
  switch (opcode & 0xf) {
  case MG_WEBSOCKET_OPCODE_TEXT:
    messageType = "text";
    break;
  case MG_WEBSOCKET_OPCODE_BINARY:
    messageType = "binary";
    break;
  case MG_WEBSOCKET_OPCODE_PING:
    messageType = "ping";
    break;
  case MG_WEBSOCKET_OPCODE_PONG:
    messageType = "pong";
    break;
  }

  // LOG("Websocket received %lu bytes of %s (%02x) data from client %u\r\n",
  //     (unsigned long)datasize,
  //     messageType,
  //     opcode,
  //     client->m_connection_number);

  if ((opcode & 0xf) == MG_WEBSOCKET_OPCODE_TEXT) {
    // text messages: we forward these to MAME
    server->send_to_mame(data, datasize);

    std::string_view message(data, datasize);
    if (message.starts_with("I")) {
      // skip sending Information messages to other clients;
      // those are server information requests.
    } else if (message.starts_with("C")) {
      // We handle the Control messages ourselves.
      // In fact we simply send the entire set of data to the client.
      LOG("'C' message: sending contents\n");
      server->send_contents();
    } else {
      // send to all connected clients except this one.
      server->send_to_all_clients(data, datasize, conn);
    }
  } else if ((opcode & 0xf) == MG_WEBSOCKET_OPCODE_PING) {
    // send a PONG message in response
    mg_websocket_write(conn, MG_WEBSOCKET_OPCODE_PONG, "pong", 4);
  }

  return 1;
}

/* Handler indicating the connection to the client is closing. */
static void ws_close_handler(const struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);
  server->lock();

  /* Get websocket client context information. */
  Connected *connected = static_cast<Connected *>(mg_get_user_connection_data(conn));
  if (!connected->is_client) {
    LOG("Server websocket connection closed, ignoring.\r\n");
    return;
  }

  WSClient *client = static_cast<WSClient *>(connected);
  client->m_connection = nullptr;

  /* DEBUG: Client has left. */
  // LOG("Client %u closing connection\r\n", client->m_connection_number);

  server->remove_client(client);

  /* Free memory allocated for client context in ws_connect_handler() call. */
  delete client;

  server->unlock();
}

static int serve_html(struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  auto lookup = [server](std::string &s) { return server->substitute(s); };
  std::stringstream templated;

  write_template(templated, server->html(), lookup, '$', '$');
  std::string result = templated.str();

  mg_send_http_ok(conn, "text/html", result.length());
  mg_write(conn, result.data(), result.length());

  return 200; /* HTTP state 200 = OK */
}

static int serve_js(struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  std::string js = server->js();
  mg_send_http_ok(conn, "text/javascript", js.length());
  mg_write(conn, js.data(), js.length());

  return 200; /* HTTP state 200 = OK */
}

struct termios orig_termios;

void reset_termios() {
  tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios);
}

int main(int argc, char *argv[]) {
  Pipe p;
  if (!p) {
    L(std::cerr << std::format("Cannot create pipe: {}", strerror(errno)) << std::endl);
    exit(1);
  }

  std::map<std::string, std::string, std::less<>> options {
    {"direct", "localhost:15112"},
    {"websocket", "localhost:8080/esqpanel/socket"},
    // {"webroot", "../../.."},  // during JS development
    {"webroot", ""},
  };

  static const char *web_server_options[] = {
  #if USE_SSL
  // #warning "Using SSL"
    "listening_ports", "8080,8443s",
  #else // ! USE_SSL
  // # warning "NO SSL"
    "listening_ports", "9090",
  #endif // USE_SSL
    "num_threads", "10",
    nullptr, nullptr,
  };
  std::map<std::string, int, std::less<>> web_server_param_indexes {
    {"listening_ports", 1},
    {"num_threads", 3},
  };

  for (int i = 1; i < argc; i++) {
    std::string_view arg(argv[i]);
    if (arg.starts_with("-")) {
      // advance and grab the value for this flag
      i++;
      std::optional<std::string_view> val;
      if (i < argc)
        val = std::string_view(argv[i]);

      auto flag = arg.substr(1);

      auto wi = web_server_param_indexes.find(flag);
      if (wi != web_server_param_indexes.end()) {
        // this is one of the web server arguments - put it in the table
        if (val.has_value()) {
          web_server_options[wi->second] = argv[i];
        } else {
          L(std::cerr << std::format("Missing value for web server flag '{}'", arg) << std::endl);
          exit(-1);
        }
        continue;
      }

      auto oi = options.find(flag);
      if (oi != options.end()) {
        if (val.has_value()) {
          std::string s_flag(flag);
          std::string s_val(val.value());
          options[s_flag] = s_val;
        } else {
          L(std::cerr << std::format("Missing value for flag '{}'", arg) << std::endl);
          exit(-1);
        }
        continue;
      }

      if (flag.starts_with("h") || flag == "?") {
        L(std::cerr << std::format("{} flags:", argv[0]) << std::endl);
        L(std::cerr << "  -listening_ports <ports>     [8080]" << std::endl);
        L(std::cerr << "  -num_threads <n>             [3]" << std::endl);
        L(std::cerr << "  -direct    <host:port>       [localhost:1552]" << std::endl);
        L(std::cerr << "  -websocket <host:port/path>  [localhost:8080/esqpanel/socket]" << std::endl);
        L(std::cerr << "  -webroot <path>              [none: serve compiled-in JS & HTML]" << std::endl);

        exit(0);
      }

      // if we get here, it's not either a web server or a mame flag!
      L(std::cerr << std::format("Unknown flag '{}'", arg) << std::endl);
      exit(-1);
    } else {
      L(std::cerr << std::format("Unknown argument '{}'", arg) << std::endl);
      exit(-1);
    }
  }

  std::string &direct = options["direct"];
  std::string &ws = options["websocket"];
  std::string &webroot = options["webroot"];

  Server server { direct, ws, webroot };

  // By default, gues it's a VFX, version 0.
  server.set_template_value("keyboard", "vfx");
  server.set_template_value("version", "0");

  /* Initialize CivetWeb library without OpenSSL/TLS support. */
  mg_init_library(0);

  /* Start the server using the advanced API. */
  struct mg_callbacks callbacks = {0};

#if USE_SSL
  callbacks.init_ssl = init_ssl;
#endif // USE_SSL

  void *user_data = &server;

  struct mg_init_data mg_start_init_data = {0};
  mg_start_init_data.callbacks = &callbacks;
  mg_start_init_data.user_data = user_data;
  mg_start_init_data.configuration_options = web_server_options;


  struct mg_error_data mg_start_error_data = {0};
  char errtxtbuf[256] = {0};
  mg_start_error_data.text = errtxtbuf;
  mg_start_error_data.text_buffer_size = sizeof(errtxtbuf);

  struct mg_context *ctx =
      mg_start2(&mg_start_init_data, &mg_start_error_data);
  if (!ctx) {
    L(std::cerr << std::format("Cannot start server: {}\r\n", errtxtbuf) << std::endl);
    mg_exit_library();
    return 1;
  }

  /* Register the websocket callback functions. */
  mg_set_websocket_handler(ctx,
    "/socket",
    ws_connect_handler,
    ws_ready_handler,
    ws_data_handler,
    ws_close_handler,
    user_data);

  mg_set_request_handler(ctx, "/", serve_html, &server);
  mg_set_request_handler(ctx, "/index.html", serve_html, &server);
  mg_set_request_handler(ctx, "/View.html", serve_html, &server);
  mg_set_request_handler(ctx, "/View.js", serve_js, &server);

  /* Let the server run. */
  // L(std::cerr << "Websocket server running" << std::endl);

#if BYCHAR
  initscr();
  cbreak();

  int c;
  while ((c = getch()) != 'q') {
    printf("Have char '%02x'\r\n", c);
    std::string s;
    switch(c) {
      // no-op for now
    }
  }
#else
  int c;
  while ((c = getchar()) != 'q') {
    printf("Have char '%02x'\r\n", c);
    std::string s;
    switch(c) {
      // no-op for now
    }
  }

#endif

  /* Stop server, disconnect all clients. Then deinitialize CivetWeb library. */
  mg_stop(ctx);
  mg_exit_library();
}
