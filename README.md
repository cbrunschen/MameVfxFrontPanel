# Overview

`MameVfxFrontPanel` offers a web interface to the Ensoniq VFX family of keybards as emulated by MAME, running
as plain HTTP. It is implemented using the [CivetWeb](https://github.com/civetweb/civetweb) embeddable
web server.

It can connect to either the websocket that's exposed by MAME's master branch at the time of writing, or the remote view support that was previously implemented in [#14131](https://github.com/mamedev/mame/pull/14131), though that has been removed, for now.

By default, `MameVfxFrontPanel` serves its contents on all local interfaces on port `9090`: You can access the view as [http://localhost:9090/](http://localhost:9090/).

You can optionally build `MameVfxFrontPanel` with OpenSSL support by specifying `USE_SSL` as `TRUE` in 
[CMakeLists.txt](CMakeLists.txt) on line 5. In that case, the build process uses `openssl` to create a
new key and a self-signed certificate, and the view can also be accessed at 
[https://localhost:8443/](https://localhost:8443/).
 
`MameVfxFrontPanel` connects to a locally running instance of MAME either through its http server's websocket on port 8080, or with the bespoke protocol on port `15112`, the [default value for MAME's `comm_localport` option](https://github.com/mamedev/mame/blob/b6df5c4970f9704449ca1c94310c30e4e6d3bc6a/src/emu/emuopts.cpp#L192) at the time of writing.

You can explicitly specify the host and port on which to listen using CivetWeb's standard `-listening_ports` command line flag:

```bash
$ MameVfxFrontPanel -listening_ports localhost:9090
```

will listen only on the loopback interface `127.0.0.1` port `9090`. You can specify multiple ports,
and SSL ports are identified by adding a suffix `s`. So

```bash
$ MameVfxFrontPanel -listening_ports 9090,9443s
```

will listen on port 9090 for HTTP and 9443 for HTTPS traffic.

You can also specify the host and port where MAME should be listening for a connection, with a websocket connection:

```bash
$ MameVfxFrontPanel -websocket some.machine:9000/esqpanel/socket
```

will attempt to connect to MAME running the http server on `some.machine` port 9000, connecting to the websocket at `/esqpanel/socket`;

```bash
$ MameVfxFrontPanel -direct some.machine:9000
```

will connect to MAME with the proposed direct connection on `some.machine` port 9000.

You can also specify both options, and `MameVfxFrontPanel` will connecct to whichever one it can.

If you're running MAME and `MameVfxFrontPanel` both on the same machine, their defaults should match,
and `MameVfxFrontPanel` should automatically connect to MAME, whichever connection it uses. This gives us a simplest case: Running

```bash
$ mame sd132 -http
```

(for MAME's master branch) or 

```bash
$ mame sd132
```

(for the proposed direct connection) in one terminal starts MAME emulating the Ensoniq SD-1/32, listening for a connection on the default port (8080 for http, 15112 for the direct connection); and running

```bash
$ MameVfxFrontPanel
```

in another terminal on the same machine starts `MameVfxFrontPanel`, connecting to MAME as started above, serving the view on [http://localhost:9090/](http://localhost:9090/).

As long as a web browser is connected to `MameVfxFrontPanel`, it will keep the connection to MAME alive. If connection to MAME is lost, `MameVfxFrontPanel`
will attempt to reconnect, once every second, until it succeeds or is stopped.

When running MAME, you can of course tell MAME which interface address and port number to listen on, using MAME's `-comm_localhost` and `-comm_localport` command line flags:

```bash
$ mame sd132 -comm_localhost 127.0.0.1 -comm_localport 9000
```

will start MAME, listening only on the loopback interface `127.0.0.1` (and thus not be accessible from any other machine) on port `9000` instead of MAME's default port `15112`. You would then need to run `MameVfxFrontPanel` to match the above:

```bash
$ MameVfxFrontPanel -direct localhost:9000
```

`MameVfxFrontPanel` currently builds on Linux with `cmake` using `clang++` 20. It requires support for `#embed` to embed the HTML and JavaScript source files into the binary.

# [`build_view`](build_view)

The project also includes the [`build_view`](build_view) directory, which contains a Python program that generates the view itself, either as JavaScript code for use in `MameVfxFrontPanel` or as individual [MAME layout files](https://docs.mamedev.org/techspecs/layout_files.html) for the `vfx`, `vfxsd` and `sd1` / `sd132` keyboards, for inclusion in MAME itself. See [`build_view/README.md`](build_view/README.md) for more details.

