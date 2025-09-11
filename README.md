`MameVfxFrontPanel` offers a web interface to the Ensoniq VFX family of keybards as emulated by MAME, running
as plain HTTP. It is implemented using the [https://github.com/civetweb/civetweb](CivetWeb) embeddable
web server.

By default, `MameVfxFrontPanel` serves its contents on all local interfaces on port `8080`: You can access the front panel as
[http://localhost:8080/] (and also at [http://localhost:8080/index.html] and, for historical reasons, at
[http://localhost:8080/FrontPanel.html]).

It connects to a locally running instance of MAME on port `15112`, the [https://github.com/mamedev/mame/blob/b6df5c4970f9704449ca1c94310c30e4e6d3bc6a/src/emu/emuopts.cpp#L192](default value for MAME's `comm_localport` option) at the time of writing.

You can explicitly specify the host and port on which to listen using CivetWeb's standard `-listening_ports` command line flag:

```MameVfxFrontPanel -listening_ports localhost:9090```

will listen only on the llopback interface `127.0.0.1` port `9090`.

You can also specify the host and port where MAME is listening for a connection, using the `-mame_host` and `-mame_port` options:

```MameVfxFrontPanel -mame_host some.machine -mame_port 9000```

will attempt to connect to MAME running on `some.machine` port 9000.

If you're running MAME and `MameVfxFrontPanel` both on the same machine, their defaults should match,
and `MameVfxFrontPanel` should automatically connect to MAME. If connection is lost, `MameVfxFrontPanel`
will attempt to reconnect, once every second, until it succeeds or is stopped.


When running MAME, you can of course tell MAME which interface address and port numberto listen on, using MAME's `-comm_localhost` and `-comm_localport` command line flags:

```mame -w -rp path/to/mame/roms sd132 -midiin default -comm_localhost 127.0.0.1 -comm_localport 9000```

will start MAME, listening only on the loopback interface `127.0.0.1` (and thus not be accessible from any other machine) on port `9000` instead of MAME's default port `15112`.


`MameVfxFrontPanel` currently builds on Linux with `cmake` using `clang++` 20. It requires support for `#embed` to embed the HTML and JavaScript source files into the binary.