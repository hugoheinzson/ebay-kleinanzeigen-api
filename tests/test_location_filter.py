from utils.location_filter import filter_listings_by_radius


def test_filter_listings_by_radius_keeps_items_within_distance():
    listings = [
        {
            "adid": "1",
            "details": {"location": {"zip": "90402", "city": "Nürnberg"}},
        },
        {
            "adid": "2",
            "details": {"location": {"zip": "20537", "city": "Hamburg"}},
        },
        {
            "adid": "3",
            "details": {},
        },
    ]

    filtered, stats = filter_listings_by_radius(listings, "90402 Nürnberg", 50)

    assert [item["adid"] for item in filtered] == ["1"]
    assert stats.radius_km == 50
    assert stats.kept_count == 1
    assert stats.excluded_ids == ["2"]
    assert stats.missing_ids == ["3"]
    assert filtered[0]["distance_km"] == 0.0


def test_filter_listings_by_radius_returns_all_without_radius():
    listings = [
        {"adid": "1", "details": {"location": {"zip": "90402"}}},
        {"adid": "2", "details": {"location": {"zip": "20537"}}},
    ]

    filtered, stats = filter_listings_by_radius(listings, "90402 Nürnberg", None)

    assert len(filtered) == 2
    assert stats.excluded_count == 0
    assert stats.kept_count == 2
