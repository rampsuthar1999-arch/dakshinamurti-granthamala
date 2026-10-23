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
| पञ्चदशी (Pañcadaśī) — श्रीमद्विद्यारण्यस्वामी, व्याख्या: स्वामी महेशानन्द गिरि | ✅ Available: 15 prakaraṇas, 1,567 ślokas, 1,530 pages |
| अनुभूतिप्रकाश (Anubhūti Prakāśa) | Planned |
| श्रीकृष्ण-सन्देश (Śrī Kṛṣṇa Sandeśa) | Planned |

## Features

- Prakaraṇa-wise reading with ślokas, their meaning, and the commentary each styled differently
- Original scanned page for every page, side by side on wide screens or full-screen with swipe and zoom
- Full-text search over the whole book in Devanagari or Roman (`kutastha`, `brahmAnanda`), with a lenient mode that tolerates common OCR errors
- Śloka index: find a verse by its opening words or by reference (e.g. `6.12`)
- Bookmarks with notes, remembers where you stopped, font size, and light/sepia/dark themes
- Every paragraph or verse can be copied, linked, or reported as a text error (opens a GitHub issue)

## Accuracy

The text was extracted automatically from the printed book's OCR layer, so there are errors, especially in Sanskrit verses and in some vowel signs (है/हे, ं/ँ).
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
