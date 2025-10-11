#include <cstdint>
#include <iostream>
#include <thread>
#include <unordered_map>
#include <functional>
#include <sstream>
#include <list>
#include <unordered_set>
#include <map>
#include <filesystem>
#include <fstream>

#include <unistd.h>
#include <poll.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <arpa/inet.h>
#include <string.h>

#include "civetweb.h"

#define HTML "FrontPanel.html"
#define JS "FrontPanel.js"

#define DEBUG 0
#if DEBUG
#define LOG(...) LOG(__VA_ARGS__)
#define LOG_FUNCTION do { LOG("%s(), state = %d\r\n", __func__, m_mame_connection_state); } while(0)
#else // DEBUG
#define LOG(...) do{}while(0)
#define LOG_FUNCTION do{}while(0)
#endif // DEBUG

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

struct WSClient {
  struct mg_connection *m_connection;
  int m_connection_number;
  bool m_ready = false;

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
    // std::cout << std::format("Sending '{}' to client {}", message, m_connection_number) << std::endl;
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
    return o << std::format("Don't know how to convert family {:d} addresses\n", pai->ai_family);
  }
}

std::ostream &operator<<(std::ostream &o, const struct addrinfo &ai) {
  return o << &ai;
}

struct Server {
  std::string mame_host;
  std::string mame_port;
  std::filesystem::path webroot;
  
  // Also used for locking.
  struct mg_context *m_mg_ctx = nullptr;

  std::unordered_set<WSClient *> m_ws_clients;
  std::map<std::string, std::string> m_template_values;

  int m_mame_socket = -1;

  int m_mame_connection_state = cs_idle;

  std::thread m_mame_thread;
  Pipe m_mame_thread_commands;

  Server(const std::string &mame_host, const std::string &mame_port, const std::string &webroot) 
  : mame_host(mame_host), mame_port(mame_port), webroot(webroot), m_mame_thread_commands() {
    if ((m_mame_thread_commands.r < 0) || (m_mame_thread_commands.w < 0)) {
      std::cerr << "!!! Failed to create pipe !!!" << std::endl;
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
    LOG_FUNCTION;
    for (const auto &c: m_ws_clients) {
      if (c->m_connection != except) c->send(data, len);
    }
    unlock();
  }

  void send_to_mame(const char *data, size_t len) {
    lock();
    LOG_FUNCTION;
    if (m_mame_socket >= 0) {
      // LOG("Sending %d to MAME\r\n", len);
      write(m_mame_socket, data, len);
      write(m_mame_socket, "\r\n", 2);
    } else {
      // LOG("No MAME socket, Sending %d to MAME\r\n", len);
    }
    unlock();
  }

  void set_mame_socket(int s) {
    lock();
    LOG_FUNCTION;
    m_mame_socket = s;
    unlock();
  }

  void reset_mame_socket() { 
    lock();
    LOG_FUNCTION;
    if (m_mame_socket >= 0) {
      close(m_mame_socket);
    }
    set_mame_socket(-1);
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

  void handle_server_info(std::string_view &message) {
    // try to parse this as server info
    // std::cout << std::format("Maybe Server info: '{}' ({})\r\n", message, message.size());
    auto b = message.begin();
    auto i = message.find("I");
    if (i == 0) {
      auto kbs = message.find_first_not_of(" \r\n\t", 1);
      if (kbs != std::string::npos) {
        auto comma = message.find(',', kbs);
        if (comma != std::string::npos) {
          auto keyboard = message.substr(kbs, comma - kbs);
          auto version = message.substr(comma + 1);

          // std::cout << std::format("Have Server info! keyboard '{}' ({}), version '{}' ({})\r\n", 
          //   keyboard, keyboard.size(), version, version.size());
          set_template_value("keyboard", keyboard);
          set_template_value("version", version);
        }
      }
    }
  }

  void set_mame_connection_state(int cs) {
    lock();
    LOG_FUNCTION;
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
    if (m_mame_connection_state == cs_idle) {
      // std::cout << "Starting MAME connection thread" << std::endl;
      set_mame_connection_state(cs_starting);
      m_mame_thread = std::thread(&Server::talk_to_mame, this);
    }
    unlock();
  }

  void stop_talking_to_mame() {
    lock();
    LOG_FUNCTION;
    if (m_mame_connection_state != cs_idle) {
      m_mame_thread_commands.write('!');
      m_mame_thread.join();
    }

    set_mame_connection_state(cs_idle);

    unlock();
  }

  void finish_talking_to_mame() {
    lock();
    LOG_FUNCTION;
    set_mame_connection_state(cs_stopping);
    reset_mame_socket();
    unlock();
    
    char c;
    // LOG("- Reading from mame command pipe\r\n");
    while (m_mame_thread_commands.read(c) > 0) { /* no-op */ }
    // LOG("- Finished reading from mame command pipe\r\n");
    return;
  }

  void talk_to_mame() {
    LOG_FUNCTION;
    set_mame_connection_state(cs_connecting);

    std::cout << "Connecting to MAME ..." << std::endl;
    while (true) {
      /* First we set up the connection to MAME */
      int sfd;
      struct addrinfo hints {0};
      struct addrinfo *result, *rp;
      hints.ai_family = AF_UNSPEC;     /* Allow IPv4 or IPv6 */
      hints.ai_socktype = SOCK_STREAM; /* Stream socket */
      hints.ai_flags = 0;
      hints.ai_protocol = 0;           /* Any protocol */

      int ar = getaddrinfo(mame_host.c_str(), mame_port.c_str(), &hints, &result);

      struct pollfd pfds[2] {0};
      m_mame_thread_commands.checkRead(pfds[0]);

      for (rp = result; rp != NULL; rp = rp->ai_next) {
        sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sfd == -1) {
          std::cout << "Failed to create socket, trying next one" << std::endl;
          continue;
        }

        // fcntl(sfd, F_SETFL, O_NONBLOCK);

        std::cout << "Trying to connect to " << rp << " ...";

        connect(sfd, rp->ai_addr, rp->ai_addrlen);

        pfds[1].fd = sfd;
        pfds[1].events = POLLOUT;

        if (poll(pfds, 2, 1000) > 0) {
          if (pfds[0].revents & POLLIN) {
            return finish_talking_to_mame();
          } else if (pfds[1].revents == POLLOUT) {
            std::cout << " Connected!" << std::endl;
            break;                  /* Success */
          }
        }

        std::cout << " Connection failed." << std::endl;
        close(sfd);
      }

      freeaddrinfo(result);           /* No longer needed */

      if (rp == NULL) {               /* No address succeeded */
        // Wait for up to 1 second - but instead of sleep(), we poll the shutdown pipe.
        if (poll(&pfds[0], 1, 1000) > 0) {
          return finish_talking_to_mame();
        }
        continue;
      }

      // Connected!

      set_mame_connection_state(cs_connected);
      send_to_all_clients("DX", 2); // clear the clients' screen(s)

      pfds[0].fd = sfd;
      pfds[0].events = POLLIN | POLLHUP;

      MessageCollector<4096> collector;
      char c;

      int nfds;

      // Request the system information
      write(sfd, "\r\n\r\nI\r\n", 7);

      // We are now ready to serve back and forth between MAME and our client(s).
      set_mame_socket(sfd);

      while (true) {
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
          close(sfd);
          return finish_talking_to_mame();
        } else {
          std::cerr << std::format("Failed to read from MAME!") << std::endl;
          break;
        }
      }

      reset_mame_socket();
      close(sfd);

      set_mame_connection_state(cs_reconnecting);
    }
  }

  bool keepalive(int sfd) {
    int written = write(sfd, "\r\n", 2);
    if (written != 2) {
      std::cerr << std::format("Keepalive write failed: {}", strerror(errno)) << std::endl;
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
          std::cerr << "Error polling MAME" << std::endl;
          return 0;
        } else if (pfds[1].revents & POLLHUP) {
          std::cerr << "Hangup polling MAME" << std::endl;
          return 0;
        } else if (pfds[1].revents & POLLIN) {
          int nread = read(m_mame_socket, &c, 1);
          return nread;
        } else {
          std::cerr << "Unexpected result polling MAME" << std::endl;
          return 0;
        }
      } else {
        std::cerr << "Failed to poll MAME" << std::endl;
        return 0;
      }
    }
  }

  std::filesystem::path html_path() {
    auto path = webroot;
    path.append(HTML);
    return path;
  }

  std::filesystem::path js_path() {
    auto path = webroot;
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
    if (webroot != "") {
      return load(js_path());
    } else {
      return jss; 
    }
  }

  std::string html() {
    if (webroot != "") {
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
      // LOG("template: found initiator '%c'\n", init);
      getline(src, s, term);
      if (src.good()) {
        dst << substitute(s);
      } else {
        // LOG("template: reached end before terminator\n");
        dst << init;
        dst << s;
      }
    } else {
      // LOG("template: reached end before initiator\n");
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
		printf("SSL data inconsistency detected\n");
		return -1;
	}

	return 0; /* let CivetWeb set up the rest of OpenSSL */
}

#endif // USE_SSL

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
  // LOG("Client %u connected\n", client->m_connection_number);

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
  // LOG("Client %u ready to receive data\n", client->m_connection_number);
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

  // LOG("Websocket received %lu bytes of %s (%02x) data from client %u\n",
  //     (unsigned long)datasize,
  //     messageType,
  //     opcode,
  //     client->m_connection_number);

  if ((opcode & 0xf) == MG_WEBSOCKET_OPCODE_TEXT) {
    // text messages: we forward these to MAME
    server->send_to_mame(data, datasize);

    std::string_view message(data, datasize);
    if (!(message.starts_with("I") || message.starts_with("C"))) {
      // send to all connected clients except this one.
      server->send_to_all_clients(data, datasize, conn);
    } else {
      // skip sending Information and Control messages to other clients;
      // those are server information requests.
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
  WSClient *client = static_cast<WSClient *>(mg_get_user_connection_data(conn));
  client->m_connection = nullptr;

  /* DEBUG: Client has left. */
  // LOG("Client %u closing connection\n", client->m_connection_number);

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

int main(int argc, char *argv[]) {
  Pipe p;
  if (!p) {
    std::cerr << std::format("Cannot create pipe: {}", strerror(errno)) << std::endl;
    exit(1);
  }

  std::map<std::string, std::string, std::less<>> options {
    {"mame_host", "localhost"},
    {"mame_port", "15112"},
    // {"webroot", "../../.."},  // during JS development
    {"webroot", ""},
  };

  static const char *web_server_options[] = {
  #if USE_SSL
  // #warning "Using SSL"
    "listening_ports", "8080,8443s",
  #else // ! USE_SSL
  // # warning "NO SSL"
    "listening_ports", "8080",
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
          std::cerr << std::format("Missing value for web server flag '{}'", arg) << std::endl;
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
          std::cerr << std::format("Missing value for flag '{}'", arg) << std::endl;
          exit(-1);
        }
        continue;
      }

      if (flag.starts_with("h") || flag == "?") {
        std::cerr << std::format("{} flags:", argv[0]) << std::endl;
        std::cerr << "  -listening_ports <ports>     [8080]" << std::endl;
        std::cerr << "  -num_threads <n>             [3]" << std::endl;
        std::cerr << "  -mame_host <host>            [localhost]" << std::endl;
        std::cerr << "  -mame_port <port>            [15112]" << std::endl;
        std::cerr << "  -webroot <path>              [none: serve compiled-in JS & HTML]" << std::endl;

        exit(0);
      }

      // if we get here, it's not either a web server or a mame flag!
      std::cerr << std::format("Unknown flag '{}'", arg) << std::endl;
      exit(-1);
    } else {
      std::cerr << std::format("Unknown argument '{}'", arg) << std::endl;
      exit(-1);
    }
  }

  std::string &mame_host = options["mame_host"];
  std::string &mame_port = options["mame_port"];
  std::string &webroot = options["webroot"];

  Server server { mame_host, mame_port, webroot };

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
    std::cerr << std::format("Cannot start server: {}\n", errtxtbuf) << std::endl;
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
  mg_set_request_handler(ctx, "/FrontPanel.html", serve_html, &server);
  mg_set_request_handler(ctx, "/FrontPanel.js", serve_js, &server);

  /* Let the server run. */
  // std::cout << "Websocket server running" << std::endl;

  struct pollfd pfd;
  p.checkRead(pfd);
  while (poll(&pfd, 1, 1000 * 1000) >= 0) {
    // nop
  }
  // std::cout << "Websocket server stopping" << std::endl;

  /* Stop server, disconnect all clients. Then deinitialize CivetWeb library. */
  mg_stop(ctx);
  mg_exit_library();
}
