# claude-code-2026-04-24-00-00-android-package-name.md
## Task: Change Android package name
### Date: 2026-04-24
### Model: Claude Sonnet 4.6

---

## OBJECTIVE

Change Android package name from `com.example.frontend_app` to `com.fyp.career_guidance`
per CLAUDE.md locked decision (Flutter package name section).

---

## FILES CHANGED

### 1. frontend/android/app/build.gradle.kts

| Field | Before | After |
|---|---|---|
| namespace | `"com.example.frontend_app"` | `"com.fyp.career_guidance"` |
| applicationId | `"com.example.frontend_app"` | `"com.fyp.career_guidance"` |

### 2. frontend/android/app/src/main/kotlin/.../MainActivity.kt

| Field | Before | After |
|---|---|---|
| package declaration | `package com.example.frontend_app` | `package com.fyp.career_guidance` |

### 3. frontend/android/app/src/main/AndroidManifest.xml

| Field | Before | After |
|---|---|---|
| android:label | `"frontend_app"` | `"Career Guidance"` |

Note: The manifest tag had no `package=` attribute — no change needed there.

---

## DIRECTORY RENAME

Old path:
```
frontend/android/app/src/main/kotlin/com/example/frontend_app/MainActivity.kt
```

New path:
```
frontend/android/app/src/main/kotlin/com/fyp/career_guidance/MainActivity.kt
```

Steps taken:
1. `mkdir -p com/fyp/career_guidance`
2. `mv com/example/frontend_app/MainActivity.kt com/fyp/career_guidance/MainActivity.kt`
3. `rm -rf com/example`

Old `com/example/` tree deleted completely.

---

## MANIFESTS CHECKED — NO CHANGES NEEDED

| File | Status |
|---|---|
| `frontend/android/app/src/debug/AndroidManifest.xml` | No package references — untouched |
| `frontend/android/app/src/profile/AndroidManifest.xml` | No package references — untouched |

---

## SEARCH RESULTS FOR REMAINING REFERENCES (Pass 1 — android only)

After the initial android-scoped task, 13 files outside `frontend/android/` still carried
old `frontend_app` references. User instructed to fix all mobile and web targets in a
follow-up session (same log).

---

## FOLLOW-UP: WEB + IOS + README CLEANUP

### Files changed

#### frontend/web/manifest.json
| Field | Before | After |
|---|---|---|
| name | `"frontend_app"` | `"Career Guidance"` |
| short_name | `"frontend_app"` | `"Career Guidance"` |
| description | `"A new Flutter project."` | `"AI-Assisted Academic Career Guidance System for Karachi students."` |

#### frontend/web/index.html
| Field | Before | After |
|---|---|---|
| `<meta name="description">` | `"A new Flutter project."` | `"AI-Assisted Academic Career Guidance System for Karachi students."` |
| `<meta name="apple-mobile-web-app-title">` | `"frontend_app"` | `"Career Guidance"` |
| `<title>` | `frontend_app` | `Career Guidance` |

#### frontend/ios/Runner/Info.plist
| Field | Before | After |
|---|---|---|
| CFBundleDisplayName | `"Frontend App"` | `"Career Guidance"` |
| CFBundleName | `"frontend_app"` | `"career_guidance"` |

#### frontend/ios/Runner.xcodeproj/project.pbxproj
| Field | Before | After |
|---|---|---|
| Runner PRODUCT_BUNDLE_IDENTIFIER (3 configs) | `com.example.frontendApp` | `com.fyp.career_guidance` |
| RunnerTests PRODUCT_BUNDLE_IDENTIFIER (3 configs) | `com.example.frontendApp.RunnerTests` | `com.fyp.career_guidance.RunnerTests` |

#### frontend/README.md
Replaced Flutter boilerplate stub with project-specific documentation: app name, targets
(Android + Web), package name, flutter run/build commands, backend URL, cold-start note.

### Final search — remaining references

Searched `frontend/` for `frontend_app`, `frontendApp`, `Frontend App` after all changes.

Remaining files (intentionally NOT touched — desktop platforms, not project targets):
- `frontend/windows/runner/Runner.rc`
- `frontend/windows/runner/main.cpp`
- `frontend/windows/CMakeLists.txt`
- `frontend/macos/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme`
- `frontend/macos/Runner.xcodeproj/project.pbxproj`
- `frontend/macos/Runner/Configs/AppInfo.xcconfig`
- `frontend/linux/runner/my_application.cc`
- `frontend/linux/CMakeLists.txt`

CLAUDE.md specifies targets as "Android + Web" only. Windows/macOS/Linux are Flutter
scaffolding only — these files will never cause a build error for the project's targets.

**Android: CLEAN. Web: CLEAN. iOS: CLEAN.**

---

## PUBSPEC.YAML CHECK

`name: fyp_career_guidance` — already correct. No changes needed.

---

## BUILD RESULT

```
flutter clean    ✓
flutter pub get  ✓ (symlink warning on Windows — non-fatal)
flutter build apk --debug

Running Gradle task 'assembleDebug'...   1398.8s
√ Built build\app\outputs\flutter-apk\app-debug.apk
```

**EXIT CODE: 0 — GREEN**

First-time build downloaded: NDK 28.2.13676358, Android SDK Build-Tools 35, Android SDK Platform 36, CMake 3.22.1. These are cached for subsequent builds.
