#include <cstdint>
#include <iostream>
#include <thread>
#include <unordered_map>
#include <functional>
#include <sstream>
#include <list>
#include <unordered_set>
#include <map>

#include <unistd.h>
#include <poll.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <arpa/inet.h>

#include "civetweb.h"

static const char html[] {
#embed "FrontPanel.html"
};

static const char js[] {
#embed "FrontPanel.js"
};

static const char WS_URL[] = "/socket";

static int connection_counter = 0;

static int pipefds[2] = {0};

struct WSClient {
  struct mg_connection *m_connection;
  int m_connection_number;
  bool m_ready = false;
  std::optional<std::string> m_showing_message;

  void send(const char *data, size_t len) {
    if (m_connection && m_ready) {
      mg_websocket_write(m_connection, MG_WEBSOCKET_OPCODE_TEXT, data, len);
    }
    m_showing_message.reset();
  }

  void send(const std::string &message) {
    send(message.data(), message.length());
  }

  void show_message(const std::string &message) {
    std::cout << std::format("Want to show '{}', ", message);
    if (!m_showing_message || message != m_showing_message.value()) {
      std::cout << "clearing screen, ";
      send("DX", 2);
      std::cout << "sending message, ";
      send(message);
      m_showing_message = message;
    } else {
      std::cout << std::format("currently showing '{}', ", m_showing_message ? m_showing_message.value() : "<nothing>");
    }
    std::cout << std::format("now showing '{}'", m_showing_message.value()) << std::endl;
  }
};

struct Server {
  std::string mame_host;
  std::string mame_port;

  // Also used for locking.
  struct mg_context *m_mg_ctx = nullptr;

  std::unordered_set<WSClient *> m_ws_clients;
  int m_mame_socket = -1;
  std::map<std::string, std::string> m_template_values;

  void lock() {
    mg_lock_context(m_mg_ctx);
  }

  void unlock() {
    mg_unlock_context(m_mg_ctx);
  }

  void send_to_all_clients(const char *data, size_t len, struct mg_connection *except = nullptr) {
    lock();
    for (const auto &c: m_ws_clients) {
      c->send(data, len);
    }
    unlock();
  }

  void send_to_mame(const char *data, size_t len) {
    lock();
    if (m_mame_socket >= 0) {
      // printf("Sending %d to MAME\r\n", len);
      write(m_mame_socket, data, len);
      write(m_mame_socket, "\r\n", 2);
    } else {
      // printf("No MAME socket, Sending %d to MAME\r\n", len);
    }
    unlock();
  }

  void set_mame_socket(int s) {
    lock();
    m_mame_socket = s;
    unlock();
  }

  void reset_mame_socket() { set_mame_socket(-1); }

  void add_client(WSClient *client) {
    lock();
    m_ws_clients.insert(client);
    unlock();
  }

  void remove_client(WSClient *client) {
    lock();
    m_ws_clients.erase(client);
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

  template<typename T>
  void show_message(T &message) {
    std::stringstream os;
    os << "DC 0 0";
    for (const auto &c : message) {
      os << std::format(" {:02x} 0", c - ' ');
    }

    lock();
    for (const auto &c: m_ws_clients) {
      c->show_message(os.str());
    }
    unlock();
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
      // printf("template: found initiator '%c'\n", init);
      getline(src, s, term);
      if (src.good()) {
        dst << substitute(s);
      } else {
        // printf("template: reached end before terminator\n");
        dst << init;
        dst << s;
      }
    } else {
      // printf("webserver: reached end before initiator\n");
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
  // printf("Client %u connected\n", client->m_connection_number);

  return 0;
}

/* Handler indicating the client is ready to receive data. */
static void ws_ready_handler(struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  /* Get websocket client context information. */
  WSClient *client = static_cast<WSClient *>(mg_get_user_connection_data(conn));
  client->m_connection = conn;
  client->m_ready = true;
  const struct mg_request_info *ri = mg_get_request_info(conn);
  (void)ri; /* in this example, we do not need the request_info */

  /* DEBUG: New client ready to receive data. */
  // printf("Client %u ready to receive data\n", client->m_connection_number);
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

  // printf("Websocket received %lu bytes of %s (%02x) data from client %u\n",
  //        (unsigned long)datasize,
  //        messageType,
  //        opcode,
  //        client->m_connection_number);

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
  printf("Client %u closing connection\n", client->m_connection_number);

  server->remove_client(client);

  /* Free memory allocated for client context in ws_connect_handler() call. */
  delete client;

  server->unlock();
}

void print_addrinfo(struct addrinfo *pai) {
  if (pai->ai_family == AF_INET) {
    struct sockaddr_in *psai = (struct sockaddr_in*)pai->ai_addr;
    char ip[INET_ADDRSTRLEN];
    if (inet_ntop(pai->ai_family, &(psai->sin_addr), ip, INET_ADDRSTRLEN) != NULL) {
        printf("IPv4: %s:%d", ip, ntohs(psai->sin_port));
    }
  } else if (pai->ai_family == AF_INET6) {
    struct sockaddr_in6 *psai = (struct sockaddr_in6*)pai->ai_addr;
    char ip[INET6_ADDRSTRLEN];
    if (inet_ntop(pai->ai_family, &(psai->sin6_addr), ip, INET6_ADDRSTRLEN) != NULL) {
        printf("IPv6: %s:%d", ip, ntohs(psai->sin6_port));
    }
  } else {
      printf("Don't know how to convert family %d addresses\n", pai->ai_family);
  }
}

template<size_t size>
struct MessageCollector {
  std::array<char, size> m_buffer;
  size_t m_received = 0;
  size_t m_message_length = 0;
  bool m_overflow = false;

  void handle(char c) {
    // printf("Received %02x, overflow=%d\r\n", c, m_overflow);
    if (m_overflow) {
      if (c == '\n') {
        // printf("Found end of overflowing message, restarting.\r\n");
        m_received = 0;
        m_overflow = false;
      } else {
        // printf("In buffer overflow, ignoring.\r\n");
      }
    } else {
      switch(c) {
        case '\r': // ignore
          // printf("ignoring CR\r\n");
          break;

        case '\n':
          // printf("LF, have a message of %ld bytes\r\n", m_received);
          m_message_length = m_received;
          m_received = 0;
          break;
        
        default:
          if (m_received >= m_buffer.size()) {
            // printf("Already have %ld of %ld characters - buffer overflow!\r\n", m_received, m_buffer.size());
            m_overflow = true;
            m_message_length = 0;
            m_received = 0;
          } else {
            m_message_length = 0;
            m_buffer[m_received++] = c;
            // printf("accumulated character %02x, now have %ld (of max %ld)\r\n", c, m_received, m_buffer.size());
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

bool keepalive(int sfd) {
  int written = write(sfd, "\r\n", 2);
  if (written != 2) {
    printf("(!K)[keepalive write failed: %d -> %d]\r\n", written, errno);
    fflush(stdout);
    return false;
  } else {
    // printf("(K)");
    fflush(stdout);
    return true;
  }
}

bool read_from_mame(int sfd, char &c) {
  int nfds;

  struct pollfd pfd {0};
  pfd.fd = sfd;
  pfd.events = POLLIN | POLLHUP;

  while (true) {
    // printf("p"); fflush(stdout);
    if ((nfds = poll(&pfd, 1, 10000)) >= 0) {
      // printf("%d", nfds); fflush(stdout);
      if (nfds == 0) {
        // timeout
        if (!keepalive(sfd)) {
          printf("!Keepalive!\r\n"); fflush(stdout);
          return false;
        }
      } else if (pfd.revents & POLLERR) {
        printf("Error\r\n"); fflush(stdout);
        return false;
      } else if (pfd.revents & POLLHUP) {
        printf("Hangup\r\n"); fflush(stdout);
        return false;
      } else if (pfd.revents & POLLIN) {
        // printf("(R)"); fflush(stdout);
        int nread = read(sfd, &c, 1);
        return nread == 1;
      } else {
        printf("Unexpected!\r\n"); fflush(stdout);
        return false;
      }
    } else {
      printf("Poll failed!\r\n"); fflush(stdout);
      return false;
    }
  }
}

void talk_to_mame(Server *server) {
  bool first_connection = true;
  while (true) {
    printf("Connecting to MAME ...\r\n");

    if (first_connection) 
      server->show_message("Connecting to MAME ...");
    else
      server->show_message("Reconnecting to MAME ...");

    /* First we set up the connection to MAME */

    int sfd;
    struct addrinfo hints {0};
    struct addrinfo *result, *rp;
    hints.ai_family = AF_UNSPEC;     /* Allow IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM; /* Stream socket */
    hints.ai_flags = 0;
    hints.ai_protocol = 0;           /* Any protocol */

    int ar = getaddrinfo(server->mame_host.c_str(), server->mame_port.c_str(), &hints, &result);

    struct pollfd pfd {0};

    for (rp = result; rp != NULL; rp = rp->ai_next) {
      sfd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
      if (sfd == -1) {
        printf("Failed to create socket, trying next one\r\n");
        continue;
      }

      // fcntl(sfd, F_SETFL, O_NONBLOCK);

      printf("Trying to connect to ");
      print_addrinfo(rp);
      printf("\r\n");

      connect(sfd, rp->ai_addr, rp->ai_addrlen);

      pfd.fd = sfd;
      pfd.events = POLLOUT;

      if (poll(&pfd, 1, 1000) == 1 && pfd.revents == POLLOUT) {
        printf("Connected!\r\n");
        break;                  /* Success */
      }

      printf("Connection failed.\r\n");
      close(sfd);
    }

    freeaddrinfo(result);           /* No longer needed */

    if (rp == NULL) {               /* No address succeeded */
      fprintf(stderr, "Could not connect.\n");
      sleep(1);
      continue;
    }

    // Connected!

    first_connection = false;

    pfd.fd = sfd;
    pfd.events = POLLIN | POLLHUP;

    MessageCollector<4096> collector;
    char c;

    int nfds;

    // Request the system information
    write(sfd, "\r\n\r\nI\r\n", 7);

    // We are now ready to serve back and forth between MAME and our client(s).
    server->set_mame_socket(sfd);

    while (true) {
      if (read_from_mame(sfd, c)) {
        collector.handle(c);
        if (collector.has_message() && collector.message_length() > 0) {
          std::string_view message(collector.message_data(), collector.message_length());
          char c = message[0];
          if (c == 'I') {
            server->handle_server_info(message);
          }

          server->send_to_all_clients(collector.message_data(), collector.message_length());
          collector.clear_message();
        }
      } else {
        printf("Failed to read from MAME!\r\n");
        break;
      }
    }

    server->reset_mame_socket();
    close(sfd);
  }
}

static int serve_html(struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  auto lookup = [server](std::string &s) { return server->substitute(s); };
  std::stringstream templated;
  write_template(templated, html, lookup, '$', '$');
  std::string result = templated.str();

  mg_send_http_ok(conn, "text/html", result.length());
  mg_write(conn, result.data(), result.length());

  return 200; /* HTTP state 200 = OK */
}

static int serve_js(struct mg_connection *conn, void *user_data) {
  Server *server = static_cast<Server *>(user_data);

  mg_send_http_ok(conn, "text/javascript", sizeof(js));
  mg_write(conn, js, sizeof(js));

  return 200; /* HTTP state 200 = OK */
}

int main(int argc, char *argv[]) {
  if (pipe(pipefds)) {
    fprintf(stderr, "Cannot create pipe: %d\n", errno);
    exit(1);
  }

  std::map<std::string, std::string, std::less<>> options {
    {"mame_host", "localhost"},
    {"mame_port", "15112"},
  };

  static const char *web_server_options[] = {
    "listening_ports", "8080",
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
      // advance and grap the value for this flag
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

  Server server { mame_host, mame_port };
  // By default, gues it's a VFX, version 0.
  server.set_template_value("keyboard", "vfx");
  server.set_template_value("version", "0");

  printf("Starting MAME connection thread\r\n");
  std::thread mame_thread(talk_to_mame, &server);

  /* Initialize CivetWeb library without OpenSSL/TLS support. */
  mg_init_library(0);

  /* Start the server using the advanced API. */
  struct mg_callbacks callbacks = {0};
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
    fprintf(stderr, "Cannot start server: %s\n", errtxtbuf);
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
  printf("Websocket server running\n");

  struct pollfd pfd;
  pfd.fd = pipefds[0];
  pfd.events = POLLIN;
  while (poll(&pfd, 1, 10000) >= 0) {
    pfd.fd = pipefds[0];
    pfd.events = POLLIN;
  }
  printf("Websocket server stopping\n");

  /* Stop server, disconnect all clients. Then deinitialize CivetWeb library.
   */
  mg_stop(ctx);
  mg_exit_library();
}
