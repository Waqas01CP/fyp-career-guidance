# Session Log — Layout Adaptivity Pass A
**Date:** 2026-04-25  
**Model:** claude-sonnet-4-6  
**Session:** claude-code-2026-04-25-22-00-layout-adaptivity-A

---

## Files Changed

| File | Change |
|---|---|
| `frontend/lib/main.dart` | Replaced `routes:` map with `onGenerateRoute:` + FadeTransition |
| `frontend/lib/screens/auth/login_screen.dart` | LayoutBuilder adaptive layout; updated `_buildFormCard` signature |
| `frontend/lib/screens/auth/signup_screen.dart` | LayoutBuilder adaptive layout; updated `_buildFormCard` signature |
| `frontend/lib/screens/onboarding/grades_input_screen.dart` | Dropdown truncation fix; errorMaxLines on mark fields |
| `frontend/lib/screens/onboarding/riasec_quiz_screen.dart` | Font size increases across 6 elements |
| `frontend/lib/screens/onboarding/riasec_complete_screen.dart` | Font size increases across 5 elements |
| `frontend/lib/screens/onboarding/grades_complete_screen.dart` | Font size increases across 4 elements |
| `frontend/lib/screens/onboarding/assessment_screen.dart` | Font size increases across 4 elements |
| `frontend/lib/screens/onboarding/assessment_complete_screen.dart` | Font size increases across 4 elements |
| `frontend/lib/screens/onboarding/carousel_screen.dart` | Font size increases across 3 elements |

---

## LayoutBuilder Breakpoints

**Threshold:** `constraints.maxHeight < 680` → `isCompact = true`

### Login (`login_screen.dart`)
| Variable | Normal (≥680) | Compact (<680) |
|---|---|---|
| `topPadding` | 32.h | 16.h |
| `vGap` (section gaps) | 20.h | 12.h |
| `cardPadding` (form card) | 28.r | 20.r |

Additional: changed `ClampingScrollPhysics` on `SingleChildScrollView`. Outer padding now `horizontal: 24.w` only (vertical handled by `topPadding`/`vGap`).

### Signup (`signup_screen.dart`)
Tighter values — more fields in the form card.
| Variable | Normal (≥680) | Compact (<680) |
|---|---|---|
| `topPadding` | 24.h | 12.h |
| `vGap` (section gaps) | 16.h | 10.h |
| `cardPadding` (form card) | 24.r | 16.r |

---

## Font Sizes Changed Per File

### `riasec_quiz_screen.dart`
| Element | Before | After |
|---|---|---|
| Likert button label | 9.sp | 14.sp |
| Dimension chip text | 10.sp | 11.sp |
| Q counter (Q1 OF 60) | 11.sp | 13.sp |
| Question text | 16.sp | 18.sp |
| Guidance panel body | 13.sp | 14.sp |
| Legend text (Answered/Unanswered) | 11.sp | 13.sp |

### `assessment_screen.dart`
| Element | Before | After |
|---|---|---|
| Subject badge | 9.sp | 11.sp |
| Question counter | 11.sp | 13.sp |
| Question text | 17.sp | 18.sp |
| Option text (A/B/C/D) | 14.sp | 15.sp |

### `riasec_complete_screen.dart`
| Element | Before | After |
|---|---|---|
| RIASEC PROFILE COMPLETE label | 9.sp | 11.sp |
| INTEREST RADAR label | 9.sp | 11.sp |
| Top-3 pill text | 12.sp | 13.sp |
| AI INSIGHT label | 9.sp | 11.sp |
| Insight body text | 13.sp | 14.sp |

### `grades_complete_screen.dart`
| Element | Before | After |
|---|---|---|
| STEP 2 OF 3 COMPLETE badge | 9.sp | 11.sp |
| MARKS SUMMARY label | 10.sp | 11.sp |
| Overall Aggregate label | 12.sp | 13.sp |
| AI INSIGHT label | 9.sp | 11.sp |
| AI insight body | 13.sp | 14.sp |

### `assessment_complete_screen.dart`
| Element | Before | After |
|---|---|---|
| PROFILE COMPLETE badge | 9.sp | 11.sp |
| SUBJECT SCORES label | 11.sp | 13.sp |
| Subject name text | 13.sp | 14.sp |
| Score percentage text | 13.sp | 14.sp |
| AI insight body | 13.sp | 14.sp |

### `carousel_screen.dart`
| Element | Before | After |
|---|---|---|
| Chip label text (INTEREST MAPPING etc.) | 10.sp | 12.sp |
| Bento cell label top (REALISTIC etc.) | 9.sp | 11.sp |
| Bento cell label bottom (INVESTIGATIVE etc.) | 9.sp | 11.sp |
| Aptitude visual label (APTITUDE MAP etc.) | 10.sp | 12.sp |

---

## Dropdown Fix Approach

**Problem:** `DropdownMenuItem` text truncated with ellipsis even when `isExpanded: true` — the popup menu has its own width constraints separate from the field.

**Fix applied in `grades_input_screen.dart`:**
- Level dropdown items: removed `overflow: TextOverflow.ellipsis`, added `overflow: TextOverflow.visible, softWrap: true`, font 13.sp → 14.sp
- Stream dropdown items: same fix applied
- Year and Board items: no ellipsis was present, left unchanged

---

## Page Transition Approach

**File:** `frontend/lib/main.dart`

Replaced static `routes:` map with `onGenerateRoute:` callback. Each route now uses `PageRouteBuilder` with:
- `FadeTransition` opacity animation
- `CurvedAnimation(curve: Curves.easeInOut)`
- `transitionDuration: Duration(milliseconds: 220)`
- All 16 routes preserved (including `/settings` and `/error`)
- `initialRoute: '/'` unchanged

---

## flutter analyze Output

```
Analyzing frontend...
No issues found! (ran in 7.4s)
```

---

## flutter run Result

Not executed this session — `flutter run` requires Android device/emulator. `flutter analyze` confirms zero compile errors. Manual device verification deferred to user.

---

## Notes

- `splash_screen.dart`: no changes required — not affected by any of the 8 changes
- CustomPainter canvas `TextStyle` in `riasec_complete_screen.dart` left unconverted (canvas context — `.sp` cannot be applied there, already noted in prior screenutil session)
- `letterSpacing` values left as raw doubles — not scaled with `.sp` (consistent with prior session convention)
