# Culinary Circles

## Challenge

You get 9 PNG images of restaurants, food, street views, and map screenshots, each labeled with a name. At first it seems random, but the names form three clean groups by first letter:

| Group | Members |
|-------|---------|
| **A** | adam, alice, alkalem |
| **B** | beatrice, bob, bruno |
| **C** | carol, catherine, cristoph |

The description hints at "your culinary circles might intersect". Once you connect those dots, the approach becomes clear.

1. Geolocate all 9 restaurants
2. For each letter-group (3 points), compute the circumcircle (the unique circle passing through all three)
3. The three circles all intersect at one common point. That point is where the answer restaurant sits.

## Most of them

Most locations were easy because of reverse image search (Google Lens / Yandex), OSM, and little bit of street view dingling

### Group A

**adam**: Reverse image search found Hofu, an Asian grill restaurant in Køge, Denmark. `55.4587798, 12.1795418`

**alice**: The storefront shows "Talbot" signage and "EBS Nenagh" in the reflection. This is the Talbot Bar in Nenagh, Ireland. `52.8618045, -8.1982565`

**alkalem**: Reverse search located Kippe 23, a restaurant in Karlsruhe, Germany. `49.0077956, 8.4204111`

### Group B

**beatrice**: A storefront with "BCHEF" signage and French menu items (Burgers de qualité, Poulet croustillant, Smashs burgers). This is the BCHEF burgers in Dijon, France. `47.3226904, 5.0382642`

**bob**: A Portuguese custard tart (pastel de nata) with the signature dark top and flaky pastry. This is original Pastéis de Belém in Lisbon, Portugal. `38.697061, -9.203222`

**bruno**: Dutch street markings and "Westersingel" road visible. Searched all streets named "Westersingel" in the Netherlands via Overpass Turbo and found it in street view. This is MAK Kitchen in Berkel en Rodenrijs, Netherlands. `51.9957398, 4.4755506`

### Group C

**carol**: A window etched with "ALLT ÄR EKOLOGISKT" (Swedish for "everything is organic") with an anchor logo, overlooking a waterfront with Stockholm's skyline. This is Skeppsbro Bakery in Stockholm, Sweden. `59.3246111, 18.0760167`

**catherine**: A Google Maps satellite view of countryside south of Edinburgh near Beecraigs Country Park. There's a cursor on the map pointing to Champany Inn, a well-known steak restaurant right by the park. `~55.9885, -3.5379`

**cristoph**: Reverse image search found a Facebook post of this location, resolving to Café Marina in Sønderborg, Denmark. `54.899355, 9.7955834`

## Plotting the circles

With all nine restaurants geolocated, compute the circumcircle for each group. You can use any tool that draws circles through three points (like geojson.io), or compute the circumcentre directly...

So one thing I noticed is circles drawn on a web map (Google Maps, OpenStreetMap) exist in Web Mercator space (EPSG:3857), not raw lat/lon. If you compute the circumcircle naively in degrees, the result will be off by tens of kilometers at this latitude. So we must do projections to Web Mercator n then compute the circles, then convert the intersection back to lat/lon

Computing the three circumcircles in Web Mercator and finding their pairwise intersections:

```
A∩B: 57.441 N, -6.573 W
A∩C: 57.561 N, -6.414 W
B∩C: 57.401 N, -6.186 W
```

All three pairwise crossings cluster within a few kilometers on the Isle of Skye, Scotland, around `57.42 N, -6.65 W`. Due to rounding in the circumcircle calculation, they don't meet at an exact single point, but the convergence zone is small enough to identify the restaurant

## Answer

Within that convergence zone on Skye, there is exactly one restaurant: The Three Chimneys in Colbost, Dunvegan, Isle of Skye (`57.4233 N, -6.6492 W`)

## Flag

```
GPNCTF{The Three Chimneys}
```
