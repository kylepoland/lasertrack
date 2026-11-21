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
