The library's export step writes this text; a solution never writes it by hand. It is
shown for reference only.

```text
mbx 1                                   format version (first line)
note "<text>"                           optional free-text note
group g<i> "<callsign>" <SIDE> leader u<k>
unit u<k> g<i> <CLASS> "<label>" <x> <z> <RANK>
wp g<i> <n> MOVE <x> <z>                also SEEK_AND_DESTROY, HOLD, GET_OUT
wp g<i> <n> GET_IN u<k>
wp g<i> <n> CYCLE
sync g<i> <n> g<j> <m>                  two synchronised waypoints
trigger t<t> area <x> <z> <a> <b> <angle> act <ACTIVATION> repeat <ONCE|REPEATEDLY> timer <NONE|COUNTDOWN min mid max|TIMEOUT min mid max> effect <NONE|LOSE|END n>
tsync t<t> g<i> <n>                     trigger synchronised with a waypoint
end
```

Groups are written in creation order, each followed by its units and waypoints;
units are numbered across the whole mission in creation order. Numbers are written
with one decimal.
