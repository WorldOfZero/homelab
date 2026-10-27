# Collection images

Primary images for collections. The enricher sets each collection's image from the file named
after it here, for example `Aviation Collection.jpg` for the collection "Aviation Collection".

- Names are matched without regard to case. Each name must be a `CollectionName` in
  `../auto-collections.json`; a test checks this.
- Formats: `.jpg`, `.jpeg`, `.png` or `.webp`. Use a 2:3 poster, for example 1000×1500.
- A collection without a file keeps whatever image Jellyfin gives it.

Images are baked into the enricher image, so redeploy the stack after adding or changing one.
See `../README.md`.
