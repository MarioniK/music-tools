# Roadmap 3.5 Runtime Parity Comparison

| Request | HTTP status | JSON parse | Keys match | Shape issues | Genres length | Top-1 | Top-N overlap | genres_pretty |
|---|---:|---|---|---|---:|---|---:|---|
| empty.classify | 400/400 | yes | yes | baseline: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty; candidate: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty | 0/0 | None/None | 0 | yes |
| fake.classify | 400/400 | yes | yes | baseline: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty; candidate: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty | 0/0 | None/None | 0 | yes |
| health | 200/200 | yes | yes | baseline: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty; candidate: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty | 0/0 | None/None | 0 | yes |
| unsupported.classify | 400/400 | yes | yes | baseline: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty; candidate: missing top-level key: message, missing top-level key: genres, missing top-level key: genres_pretty | 0/0 | None/None | 0 | yes |
| upload.classify | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-1 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-10 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-2 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-3 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-4 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-5 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-6 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-7 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-8 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |
| upload.repeat-9 | 200/200 | yes | yes | none | 8/8 | electronic/electronic | 8 | yes |

```json
[
  {
    "name": "empty.classify",
    "http_status": {
      "baseline": "400",
      "candidate": "400",
      "match": true
    },
    "time_total": {
      "baseline": "0.002545",
      "candidate": "0.001995"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "error",
        "ok"
      ],
      "candidate": [
        "error",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ],
      "candidate": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ]
    },
    "genres_length": {
      "baseline": 0,
      "candidate": 0,
      "match": true
    },
    "genres_values": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "top_1_genre": {
      "baseline": null,
      "candidate": null,
      "match": false
    },
    "top_n_overlap": {
      "count": 0,
      "baseline_count": 0,
      "candidate_count": 0,
      "values": []
    },
    "genres_pretty": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {},
      "candidate": {}
    }
  },
  {
    "name": "fake.classify",
    "http_status": {
      "baseline": "400",
      "candidate": "400",
      "match": true
    },
    "time_total": {
      "baseline": "0.168435",
      "candidate": "0.083204"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "error",
        "ok"
      ],
      "candidate": [
        "error",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ],
      "candidate": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ]
    },
    "genres_length": {
      "baseline": 0,
      "candidate": 0,
      "match": true
    },
    "genres_values": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "top_1_genre": {
      "baseline": null,
      "candidate": null,
      "match": false
    },
    "top_n_overlap": {
      "count": 0,
      "baseline_count": 0,
      "candidate_count": 0,
      "values": []
    },
    "genres_pretty": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {},
      "candidate": {}
    }
  },
  {
    "name": "health",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "0.001957",
      "candidate": "0.001733"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "ok"
      ],
      "candidate": [
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ],
      "candidate": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ]
    },
    "genres_length": {
      "baseline": 0,
      "candidate": 0,
      "match": true
    },
    "genres_values": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "top_1_genre": {
      "baseline": null,
      "candidate": null,
      "match": false
    },
    "top_n_overlap": {
      "count": 0,
      "baseline_count": 0,
      "candidate_count": 0,
      "values": []
    },
    "genres_pretty": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {},
      "candidate": {}
    }
  },
  {
    "name": "unsupported.classify",
    "http_status": {
      "baseline": "400",
      "candidate": "400",
      "match": true
    },
    "time_total": {
      "baseline": "0.003325",
      "candidate": "0.001682"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "error",
        "ok"
      ],
      "candidate": [
        "error",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ],
      "candidate": [
        "missing top-level key: message",
        "missing top-level key: genres",
        "missing top-level key: genres_pretty"
      ]
    },
    "genres_length": {
      "baseline": 0,
      "candidate": 0,
      "match": true
    },
    "genres_values": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "top_1_genre": {
      "baseline": null,
      "candidate": null,
      "match": false
    },
    "top_n_overlap": {
      "count": 0,
      "baseline_count": 0,
      "candidate_count": 0,
      "values": []
    },
    "genres_pretty": {
      "baseline": [],
      "candidate": [],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {},
      "candidate": {}
    }
  },
  {
    "name": "upload.classify",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "7.323479",
      "candidate": "6.559398"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-1",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "6.288453",
      "candidate": "6.142238"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-10",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "8.278133",
      "candidate": "6.002572"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-2",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "6.594396",
      "candidate": "6.035802"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-3",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "6.710262",
      "candidate": "5.865909"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-4",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "7.494378",
      "candidate": "6.128669"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-5",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "7.420385",
      "candidate": "5.994081"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-6",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "6.549897",
      "candidate": "6.183149"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-7",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "6.510892",
      "candidate": "6.308418"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-8",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "6.725115",
      "candidate": "6.138334"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  },
  {
    "name": "upload.repeat-9",
    "http_status": {
      "baseline": "200",
      "candidate": "200",
      "match": true
    },
    "time_total": {
      "baseline": "7.525425",
      "candidate": "6.117546"
    },
    "json_parseability": {
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_error": null,
      "candidate_error": null
    },
    "top_level_keys": {
      "baseline": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "candidate": [
        "genres",
        "genres_pretty",
        "message",
        "ok"
      ],
      "match": true
    },
    "shape_issues": {
      "baseline": [],
      "candidate": []
    },
    "genres_length": {
      "baseline": 8,
      "candidate": 8,
      "match": true
    },
    "genres_values": {
      "baseline": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "candidate": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ],
      "match": true
    },
    "top_1_genre": {
      "baseline": "electronic",
      "candidate": "electronic",
      "match": true
    },
    "top_n_overlap": {
      "count": 8,
      "baseline_count": 8,
      "candidate_count": 8,
      "values": [
        "electronic",
        "indie",
        "rock",
        "indie rock",
        "alternative",
        "electro",
        "pop",
        "electronica"
      ]
    },
    "genres_pretty": {
      "baseline": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "candidate": [
        "indie rock",
        "alternative rock",
        "electronic",
        "indie",
        "rock",
        "alternative",
        "electro",
        "pop"
      ],
      "match": true
    },
    "scores_by_genre": {
      "baseline": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.195,
        "indie rock": 0.1836,
        "alternative": 0.1556,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      },
      "candidate": {
        "electronic": 0.3894,
        "indie": 0.3884,
        "rock": 0.1951,
        "indie rock": 0.1836,
        "alternative": 0.1557,
        "electro": 0.1237,
        "pop": 0.1012,
        "electronica": 0.0754
      }
    }
  }
]
```
