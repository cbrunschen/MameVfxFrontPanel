-- file is the layout file object
-- set a function to call after resolving tags
file:set_resolve_tags_callback(
  function ()
    -- file.device is the device that caused the layout to be loaded
    -- in this case, it's the esqpanel2x40_vfx object.

    for view_name, view in pairs(file.views) do
      install_slider_callbacks(view)

      add_vertical_slider(view, "slider_volume", "slider_knob_volume", "analog_volume")
      add_vertical_slider(view, "slider_data_entry", "slider_knob_data_entry", "analog_data_entry")

      -- TODO: Display a warning about how to enable sliders
      -- view.items["warning"]:set_state(0)
    end
  end
)

-----------------------------------------------------------------------
-- Simplified Slider library starts.
-- Can be copied as-is to other layouts.
-- It is simplified from its source:
-- * This one never reads from the port, only writes to it.
-- * Only when clickling on the knob itself does it start to drag the knob.
-- * The value is calculated based on the position of the knob within the click area.
-----------------------------------------------------------------------
local sliders = {}   -- Stores slider information.
local pointers = {}  -- Tracks pointer state.

function clamp(x)
  if x < 0 then return 0 elseif x > 1023 then return 1023 else return x end
end

-- The knob's Y position must be animated using <animate inputtag="{port_name}">.
-- The click area's vertical size must exactly span the range of the
-- knob's movement.
function add_vertical_slider(view, clickarea_id, knob_id, port_name)
  local slider = {}

  slider.clickarea = view.items[clickarea_id]
  if slider.clickarea == nil then
    emu.print_error("Slider element: '" .. clickarea_id .. "' not found.")
    return
  end

  slider.knob = view.items[knob_id]
  if slider.knob == nil then
    emu.print_error("Slider knob element: '" .. knob_id .. "' not found.")
    return
  end

  local port = file.device:ioport(port_name)
  if port == nil then
    emu.print_error("Port: '" .. port_name .. "' not found.")
    return
  end

  slider.field = nil
  for k, val in pairs(port.fields) do
    slider.field = val
    break
  end
  if slider.field == nil then
    emu.print_error("Port: '" .. port_name .."' does not seem to be an IPT_ADJUSTER.")
    return
  end

  table.insert(sliders, slider)
end

local function pointer_updated(type, id, dev, x, y, btn, dn, up, cnt)
  -- If a button is not pressed, reset the state of the current pointer.
  if btn & 1 == 0 then
    pointers[id] = nil
    return
  end

  -- If a button was just pressed, find the affected slider, if any.
  if dn & 1 ~= 0 then
    for i = 1, #sliders do
      if sliders[i].knob.bounds:includes(x, y) then
        local clickarea = sliders[i].clickarea
        local knob = sliders[i].knob
        local dy = y - knob.bounds.y0
        pointers[id] = {
          selected_slider = i,
          dy = dy -- position within the knob where it was clicked
        }
        break
      end
    end
  end

  -- If there is no slider selected by the current pointer, we are done.
  if pointers[id] == nil then
    return
  end

  -- A slider is selected. Update state and, indirectly, slider knob position,
  -- based on the pointer's Y position. The attached IO field must be
  -- an IPT_ADJUSTER with a range of 0-1023.

  local pointer = pointers[id]
  local slider = sliders[pointer.selected_slider]
  local knob = slider.knob
  local clickarea = slider.clickarea

  local yy = y - pointer.dy
  local fraction = (yy - clickarea.bounds.y0) / (clickarea.bounds.height - knob.bounds.height)
  local new_value = 1023 * (1 - fraction)
  new_value = math.floor(new_value + 0.5)
  clamped_value = clamp(new_value)
  slider.field.user_value = clamped_value
end

local function pointer_left(type, id, dev, x, y, up, cnt)
  pointers[id] = nil
end

local function pointer_aborted(type, id, dev, x, y, up, cnt)
  pointers[id] = nil
end

local function forget_pointers()
  pointers = {}
end

function install_slider_callbacks(view)
  view:set_pointer_updated_callback(pointer_updated)
  view:set_pointer_left_callback(pointer_left)
  view:set_pointer_aborted_callback(pointer_aborted)
  view:set_forget_pointers_callback(forget_pointers)
end
-----------------------------------------------------------------------
-- Slider library ends.
-----------------------------------------------------------------------


