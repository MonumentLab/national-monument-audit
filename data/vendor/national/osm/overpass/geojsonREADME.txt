Exported from:
http://overpass-turbo.eu/


Query to get the "Ways"

{{geocodeArea:United States}}->.searchArea;
( 
  way["historic"="monument"](area.searchArea);
);
out center meta;


Query for Historic Monument: https://wiki.openstreetmap.org/wiki/Tag%3Ahistoric%3Dmonument

area["name"="United States"]->.boundaryarea;
(
nwr(area.boundaryarea)[historic=monument];
);
out meta;



Query for Historic Memorial (subset): https://wiki.openstreetmap.org/wiki/Key:memorial

area["name"="United States"]->.boundaryarea;
(
nwr(area.boundaryarea)[memorial~"(statue|war\_memorial|plaque|obelisk|stele|sculpture)"];
);
out meta;
