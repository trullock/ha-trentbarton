# Trent-Barton live times for Home Assistant

## Installation

Get stopid from: https://www.trentbarton.co.uk/services/indigo/live (or a different bus service)

Example `configuration.yaml`:

```
trentbarton:
  - service: indigo
    stopid: 1234
    num_buses: 5
  - service: indigo
    stopid: 4321
    num_buses: 5
```