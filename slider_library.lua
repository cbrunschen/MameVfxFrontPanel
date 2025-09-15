-----------------------------------------------------------------------
-- Slider library starts.
-- Can be copied as-is to other layouts.
-----------------------------------------------------------------------
local sliders = {}   -- Stores slider information.
local pointers = {}  -- Tracks pointer state.

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
        pointers[id] = {
          selected_slider = i,
          relative = true,
          start_y = y,
          start_value = sliders[i].field.user_value }
        break
      elseif sliders[i].clickarea.bounds:includes(x, y) then
        pointers[id] = {
          selected_slider = i,
          relative = false }
        break
      end
    end
  end

  -- If there is no slider selected by the current pointer, we are done.
  if pointers[id] == nil then
    return
  end

  -- A slider is selected. Update state and, indirectly, slider knob position,
  -- based on the pointer's Y position. It is assumed the attached IO field is
  -- an IPT_ADJUSTER with a range of 0-100 (the default).

  local pointer = pointers[id]
  local slider = sliders[pointer.selected_slider]

  local knob_half_height = slider.knob.bounds.height / 2
  local min_y = slider.clickarea.bounds.y0 + knob_half_height
  local max_y = slider.clickarea.bounds.y1 - knob_half_height

  local new_value = 0
  if pointer.relative then
    -- User clicked on the knob. The new value will depend on how much the
    -- knob was dragged.
    new_value = pointer.start_value - 100 * (y - pointer.start_y) / (max_y - min_y)
  else
    -- User clicked elsewhere on the slider. The new value will depend on
    -- the absolute position of the click.
    new_value = 100 - 100 * (y - min_y) / (max_y - min_y)
  end

  new_value = math.floor(new_value + 0.5)
  emu.print_error("layout calculated new slider value as " .. new_value)
  if new_value < 0 then new_value = 0 end
  if new_value > 100 then new_value = 100 end
  emu.print_error(" and limited it to " .. new_value .. "\r\n")
  slider.field.user_value = new_value
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
