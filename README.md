# दक्षिणामूर्ति ग्रन्थमाला · Dakshinamurti Granthamala

A free, static web reader for the Vedānta publications of **Shri Dakshinamurti Math Prakashan, Varanasi** (श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी).

**Live site:** https://rampsuthar1999-arch.github.io/dakshinamurti-granthamala/

## Credits

All content in this app (text and page scans) comes from books published by **Shri Dakshinamurti Math Prakashan, Varanasi**.
The commentary is by **Shrotriya Brahmanishtha Acharya Mahamandaleshwar Shri 108 Swami Maheshananda Giri Ji Maharaj**.
All credit and rights belong to Shri Dakshinamurti Math. This is a non-commercial digital edition made to make study easier.

## Books

| Book | Status |
|---|---|
| पञ्चदशी (Pañcadaśī) — श्रीमद्विद्यारण्यस्वामी | ✅ 15 prakaraṇas · 1,567 ślokas · 1,530 pages |
| अनुभूतिप्रकाशः (Anubhūti Prakāśa) — श्रीमद्विद्यारण्यस्वामी, verse commentary on 12 Upaniṣads | ✅ 20 adhyāyas · 2,791 ślokas · 1,826 pages |
| श्रीकृष्ण-सन्देश (Śrī Kṛṣṇa Sandeśa) — commentary on the Bhagavad Gītā | ✅ 18 adhyāyas · 668 of 700 ślokas indexed · 1,673 pages |

| गौडपादसार (Gauḍapāda Sāra) — माण्डूक्य-उपनिषत्-कारिका व्याख्या, भाग १–२ | ✅ 4 prakaraṇas (Āgama by mantra/kārikā group) · OCR of phone scans |
| बोधसारः (Bodhasāra) — श्रीमदाचार्यनरहरि, दीप्ति टीका | ✅ 61 prakaraṇas · 1,335 verses (running numbers) |
| नैष्कर्म्यसिद्धिः (Naiṣkarmya Siddhi) — श्रीमत्सुरेश्वराचार्य, भावतत्त्वप्रकाशिका | ✅ 4 adhyāyas · OCR |
| शिवानन्दलहरी (Śivānanda Laharī) — श्रीमद्भगवत्पादाचार्य | ✅ 100 ślokas with Hindi commentary + Sanskrit ṭīkā · OCR |
| श्रीशिवमहिम्नःस्तोत्रम् (Śiva Mahimnaḥ Stotram) — श्रीपुष्पदन्ताचार्य | ✅ śloka-wise commentary · OCR |
| कैवल्योपनिषद् (Kaivalya Upaniṣad) | ✅ 116 kathās · OCR |
| दहरविद्या (Dahara Vidyā) | ✅ 17 pravachanas |
| श्वेतकेतुविद्या (Śvetaketu Vidyā) | ✅ 51 pravachanas |
| चिदानन्दलहरी (Cidānanda Laharī) | ✅ 58 pravachanas + 2 appendices |
| श्रीपुरुषोत्तमयोग (Puruṣottama Yoga) | ✅ 20 pravachanas |
| शिवसंकल्पसूक्त (Śiva Saṅkalpa Sūkta) | ✅ 62 topics |

Commentaries and discourses are by Swami Maheshananda Giri Ji Maharaj, except where noted (Bodhasāra's Dīpti ṭīkā by Ācārya Divākara; Naiṣkarmya Siddhi edited and translated by Swami Prajñānānanda Sarasvatī under his direction).

## Features

- Prakaraṇa-wise reading with ślokas, their meaning, and the commentary each styled differently
- Original scanned page for every page, side by side on wide screens or full-screen with swipe and zoom
- Full-text search over the whole book in Devanagari or Roman (`kutastha`, `brahmAnanda`), with a lenient mode that tolerates common OCR errors
- Śloka index: find a verse by its opening words or by reference (e.g. `6.12`)
- Jump straight to any verse from the home page: `पञ्चदशी ९.२`, `anubhuti 3.14`, `gita 2.47`, or link to `#/b/<book>/v/9.2`
- Installable as a phone app (PWA), with a button to save a whole book (text, optionally scans) for offline reading
- Bookmarks with notes, remembers where you stopped, font size, and light/sepia/dark themes
- Every paragraph or verse can be copied, linked, or reported as a text error (opens a GitHub issue)

## Accuracy

- **Pañcadaśī:** from the PDF's existing OCR layer, so there are errors, especially in Sanskrit verses and some vowel signs (है/हे, ं/ँ).
- **Anubhūti Prakāśa:** converted from the Kruti-Dev-family legacy fonts, so it is very close to the printed text.
- **Books marked OCR** (Naiṣkarmya Siddhi, Śivānanda Laharī, Śiva Mahimnaḥ Stotram, Kaivalya Upaniṣad) were read from page images with Tesseract, so expect more errors there. The other new books were converted from legacy fonts (Narad/Shiva, Chandini, NewDelhi, Kundli, Walkman-Chanakya).
- **Śrī Kṛṣṇa Sandesh:** chapters 2 and 10–18 were converted from legacy fonts (including pages whose font codes were shifted). Chapter 1, chapters 3–9 and the front matter were OCR'd with Tesseract, so expect more errors there.
Corrections are welcome: tap any paragraph and choose **त्रुटि** (error).

## Structure

```
index.html, app.js, style.css   – the app (plain HTML/JS, no build step)
data/library.json               – list of books
data/<book>/book.json           – sections, page mapping
data/<book>/<section>.json      – text blocks: [type, pdfPage, text, ślokaNo?]
data/<book>/slokas.json         – śloka index
pages/<book>/<n>.webp           – page scans
tools/                          – scripts used to extract the text from the PDF
```

Block types: `v` verse, `tr` meaning of a verse, `p` commentary paragraph, `e` end-of-chapter line; a trailing `c` marks a paragraph continued from the previous page.
