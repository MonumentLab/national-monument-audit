Exported from:
http://overpass-turbo.eu/

{{geocodeArea:United States}}->.searchArea;
( 
  way["historic"="monument"](area.searchArea);
);
out center meta;



Had to manually export monuments from overpass that were type=Way since quickOSM only gave us type=Node