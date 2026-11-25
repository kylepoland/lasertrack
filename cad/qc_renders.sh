#!/bin/zsh
# QC renders for every model. Run from cad/ after rebuilding all models:
#   find out/renders -name '*.png' -delete && zsh qc_renders.sh
set -e
r() { uv run python render.py "$@" >/dev/null; }   # a function, not $VAR: zsh won't split it

# --- Cartridge and slot ---
r cartridge out/cartridge_front.stl out/cartridge_back.stl
r cartridge_exploded out/cartridge_front.stl:20 out/cartridge_back.stl
r front_half out/cartridge_front.stl
r back_half out/cartridge_back.stl
r section_top out/cartridge_section_top_front.stl out/cartridge_section_top_back.stl --focus 35.6,25.2,6.25,16
r section_bottom out/cartridge_section_bottom_front.stl out/cartridge_section_bottom_back.stl --focus 44.7,-25.2,6.25,16
r back_detent out/cartridge_back.stl --focus 30,-25,0,20 --view back
r back_track out/cartridge_back.stl --focus 50.5,-22,4,24
r slot out/slot.stl --yup
r slot_assembly out/slot.stl out/slot_plunger.stl out/cartridge_front.stl:0.2 out/cartridge_back.stl:0.2 --yup
r slot_exploded out/slot.stl out/slot_plunger.stl out/cartridge_front.stl:0,45,0.2 out/cartridge_back.stl:0,45,0.2 --yup
S=out/slot_section
r slot_section_plunger ${S}_plunger_slot.stl ${S}_plunger_plunger.stl ${S}_plunger_front.stl ${S}_plunger_back.stl --focus 30,-24,2,22
r slot_section_rail ${S}_rail_slot.stl ${S}_rail_plunger.stl ${S}_rail_front.stl ${S}_rail_back.stl --focus 48,-21,5,16 --view top

# --- Cartridge with PCB, slot with pogo pins ---
PCB="#2f7d4f"; GOLD="#d4af37"; PIN="#b8b8b8"
r cartridge_pcb out/cartridge_pcb_front.stl out/cartridge_pcb_back.stl out/cartridge_pcb_board.stl@$PCB out/cartridge_pcb_pads.stl@$GOLD
r cartridge_pcb_exploded out/cartridge_pcb_front.stl:20 out/cartridge_pcb_back.stl out/cartridge_pcb_board.stl:0,-15,0@$PCB out/cartridge_pcb_pads.stl:0,-15,0@$GOLD
r cartridge_pcb_front_half out/cartridge_pcb_front.stl
r cartridge_pcb_back_half out/cartridge_pcb_back.stl out/cartridge_pcb_board.stl@$PCB
r cartridge_pcb_bottom out/cartridge_pcb_front.stl out/cartridge_pcb_back.stl out/cartridge_pcb_board.stl@$PCB out/cartridge_pcb_pads.stl@$GOLD --focus 0,-31,6.25,105 --view bottom
r cartridge_pcb_bottom_end out/cartridge_pcb_front.stl out/cartridge_pcb_back.stl out/cartridge_pcb_board.stl@$PCB out/cartridge_pcb_pads.stl@$GOLD --focus 38,-31,6.25,22 --view bottom
C=out/cartridge_pcb_section
r cartridge_pcb_section_mid ${C}_mid_front.stl ${C}_mid_back.stl ${C}_mid_board.stl@$PCB --focus 0,-28,6.25,16
r cartridge_pcb_section_seat ${C}_seat_front.stl ${C}_seat_back.stl ${C}_seat_board.stl@$PCB --focus 30,-27,6.25,16
r cartridge_pcb_section_end ${C}_end_front.stl ${C}_end_back.stl ${C}_end_board.stl@$PCB --focus 40,-28,6.25,16
r slot_pcb out/slot_pcb.stl --yup
r slot_pcb_assembly out/slot_pcb.stl out/slot_pcb_plunger.stl out/slot_pcb_board.stl@$PCB out/slot_pcb_pins.stl@$PIN out/slot_pcb_screws.stl@$PIN out/cartridge_pcb_front.stl:0.2 out/cartridge_pcb_back.stl:0.2 out/cartridge_pcb_board.stl:0,0.2,0.2@$PCB --yup
r slot_pcb_exploded out/slot_pcb.stl out/slot_pcb_board.stl:0,-15,0@$PCB out/slot_pcb_pins_free.stl:0,-15,0@$PIN out/slot_pcb_screws.stl:0,-25,0@$PIN out/cartridge_pcb_front.stl:0,45,0.2 out/cartridge_pcb_back.stl:0,45,0.2 --yup
r slot_pcb_underside out/slot_pcb.stl out/slot_pcb_board.stl@$PCB out/slot_pcb_pins.stl@$PIN out/slot_pcb_screws.stl@$PIN --focus 0,-36,1,130 --view bottom
P=out/slot_pcb_section
r slot_pcb_section_pin ${P}_pin_slot.stl ${P}_pin_board.stl@$PCB ${P}_pin_pins.stl@$PIN ${P}_pin_front.stl ${P}_pin_back.stl ${P}_pin_pcb.stl@$PCB --focus 21,-31,4,24
r slot_pcb_section_pin_close ${P}_pin_slot.stl ${P}_pin_board.stl@$PCB ${P}_pin_pins.stl@$PIN ${P}_pin_front.stl ${P}_pin_back.stl ${P}_pin_pcb.stl@$PCB --focus 21,-31.5,6.2,9
r slot_pcb_section_screw ${P}_screw_slot.stl ${P}_screw_board.stl@$PCB ${P}_screw_screws.stl@$PIN ${P}_screw_front.stl ${P}_screw_back.stl --focus 14,-31,0,30

# --- Box (Z up, front at -Y: pass --zup) ---
O=out
MINT="#8fd3bd"; TAN="#cfae7f"; LIME="#c6e83a"; WHITE="#f1f0ec"; ORANGE="#f0602c"; BLACK="#2a2a2a"
GREY="#9aa0a6"; GREEN="#2f7d4f"; BLUE="#3a6fb0"; CART="#5a5048"
SHELL=($O/box_top_front.stl@$MINT $O/box_top_back.stl@$MINT $O/box_bottom.stl@$TAN $O/box_plate.stl@$LIME
       $O/box_front_panel.stl@$WHITE $O/box_back_panel.stl@$WHITE $O/box_caps.stl@$WHITE
       $O/box_knob_placed.stl@$ORANGE $O/box_feet.stl@$BLACK)
INSIDE=($O/box_bought_slot.stl@$WHITE $O/box_bought_cartridge_front.stl@$CART $O/box_bought_cartridge_back.stl@$CART)
GUTS=($O/box_bought_pi.stl@$GREEN $O/box_bought_pi_plugs.stl@$GREY $O/box_bought_reader.stl@$BLUE
      $O/box_reader_cradle.stl@$GREY $O/box_bought_lcd.stl@$BLUE $O/box_bought_button_board.stl@$GREEN
      $O/box_bought_encoder.stl@$GREY $O/box_bought_dc_jack.stl@$GREY $O/box_bought_av_jack.stl@$GREY
      $O/box_bought_hdmi.stl@$GREY $O/box_bought_toggle.stl@$GREY $O/box_bought_plungers.stl@$GREY)

r box --zup $SHELL $INSIDE
r box_open --zup $O/box_bottom.stl@$TAN $O/box_plate.stl@$LIME $O/box_front_panel.stl@$WHITE \
  $O/box_back_panel.stl@$WHITE $O/box_caps.stl@$WHITE $O/box_knob_placed.stl@$ORANGE $O/box_feet.stl@$BLACK $INSIDE $GUTS
r box_exploded --zup $O/box_top_front.stl:0,0,60@$MINT $O/box_top_back.stl:0,0,60@$MINT \
  $O/box_bottom.stl:0,0,-40@$TAN $O/box_plate.stl@$LIME $O/box_front_panel.stl:0,-50,0@$WHITE \
  $O/box_back_panel.stl:0,50,0@$WHITE $O/box_caps.stl:0,-70,0@$WHITE $O/box_knob_placed.stl:0,-80,0@$ORANGE \
  $O/box_feet.stl:0,0,-60@$BLACK $INSIDE
for part in top_front top_back bottom plate front_panel back_panel reader_cradle; do
  r part_$part --zup $O/box_$part.stl
done
r part_button_cap $O/box_button_cap.stl
r part_knob $O/box_knob.stl
r part_foot $O/box_foot.stl

# Sections: box_section_<cut>_*.stl, coloured by part. sec CUT NAME render-args...
colour() {
  case $1 in
    *top_*) echo $MINT;; *bottom*) echo $TAN;; *plate*) echo $LIME;; *panel*|*caps*|*slot*) echo $WHITE;;
    *knob*) echo $ORANGE;; *feet*) echo $BLACK;; *cartridge*) echo $CART;; *pi*) echo $GREEN;;
    *reader*|*lcd*) echo $BLUE;; *) echo $GREY;;
  esac
}
sec() {
  local cut=$1 name=$2; shift 2
  local files=(); for f in $O/box_section_${cut}_*.stl; do files+=("$f@$(colour $f)"); done
  r $name --zup $files "$@"
}
sec x0 box_section_x0 --focus 0,-20,40,110 --view side          # slot, cartridge, reader
sec x0 box_section_front --focus 0,-62,40,40 --view side        # front panel, caps, button board
sec pi box_section_pi --focus 88,30,40,120 --view side          # Pi under the top curl
sec screw box_section_screw --focus 105,12,30,40 --view back    # column + plate + tab
sec slot box_section_slot --focus 0,-30,45,150 --view front     # across the slot
sec slot box_section_slot_right --focus 85,-30,38,80 --view front
