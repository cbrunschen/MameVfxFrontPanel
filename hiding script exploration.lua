-- file is the layout file object
-- set a function to call after resolving tags
file:set_resolve_tags_callback(
  function ()
    -- file.device is the device that caused the layout to be loaded
    -- in this case, it's the esqpanel2x40_vfx object.
    -- look up the two I/O ports we need to be able to read
    
    local buttons_0 = file.device:ioport("buttons_0")
    local buttons_32 = file.device:ioport("buttons_32")

    shortname = file.device.owner.shortname
    emu.print_error(string.format("device.owner.shortname = '%s'", shortname))
    
    local hasSeq = string.find(shortname, "sd")
    if hasSeq then emu.print_error("has sequencer") else emu.print_error("no sequencer") end

    local hasBankSet = string.find(shortname, "1")
    if hasBankSet then emu.print_error("has bank set") else emu.print_error("has cart") end

    local has32Voices = string.find(shortname, "32")
    if has32Voices then emu.print_error("has 32 voices") else emu.print_error("has 21 voices") end

    -- in the state callback we need to check both that hasSeq has the expected value, and read from the ioport.
    function make_state_callback(expected, port, bit)
      return function()
        emu.print_debug(string.format("checking state: expect %s, , have %s", expected, actual))
        if expected ~= actual then
          emu.print_debug(", returning 2\r\n")
          return 2  -- neither 0 nor 1, so should hide both button images
        else
          local value = port:read()
          emu.print_debug(", checking port, value is " .. value .. "\r\n")
          if value & (1 << bit) ~= 0 then return 1 else return 0 end
        end
      end
    end

    local panel = file.views["Panel"]

    item = panel.items["button_51__seq__C_hasSeq_True"]
    if not item then emu.print_error("Failed to find item") end

    item:set_element_state_callback(
      make_state_callback(true, hasSeq, buttons_32, 19)
    )
  end
)
