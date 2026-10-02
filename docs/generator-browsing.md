# Generator browsing

The Generator search panel supports browsing the full JP Ver.4.0 QR2_INFO dataset without entering a query.

- All 2,143 entries are available when the search box is empty.
- Results are rendered incrementally in batches of 80 as the user scrolls.
- Selecting a result while browsing does not collapse the result list into a search for that selected reward.
- Entering a Japanese name, English alias, Item ID, Type, or Flag filters the same dataset; filtered results are also loaded incrementally.

The batching is intentional so initial page load does not create thousands of result-row DOM nodes at once, especially on mobile browsers.
