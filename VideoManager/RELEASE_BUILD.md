# Release Build

This project is configured so a future session can build an installable
release APK without rediscovering the signing setup.

## Signing

`app/build.gradle` loads signing properties in this order:

1. `./keystore.properties` in this project, if present.
2. `/Users/kys1207/AndroidStudioProjects/MyHome/keystore.properties` as the fallback.

The fallback file points to the MyHome release keystore. Do not copy passwords
into this repository or into chat.

The release certificate currently verifies as:

```text
CN=MyHome, OU=MyHome, O=MyHome, L=Seoul, ST=Seoul, C=KR
```

## One Command

Run:

```bash
./scripts/build_release.sh
```

The script runs:

1. `./gradlew testDebugUnitTest`
2. `./gradlew assembleRelease`
3. `apksigner verify --verbose --print-certs`

Output APK:

```text
app/build/outputs/apk/release/app-release.apk
```

## Manual Commands

If the script cannot be used:

```bash
./gradlew testDebugUnitTest
./gradlew assembleRelease
/Users/kys1207/Library/Android/sdk/build-tools/35.0.1/apksigner verify --verbose --print-certs app/build/outputs/apk/release/app-release.apk
```

If a debug APK is already installed on the phone, uninstall it before installing
this release APK because the debug and release signing keys are different.

## Firebase App Distribution

The app module is configured for Firebase App Distribution on the `release`
build type. The Firebase config file is expected at:

```text
app/google-services.json
```

For local distribution, authenticate with the Firebase CLI first:

```bash
firebase login
```

Then upload a signed release APK:

```bash
./gradlew :app:assembleRelease :app:appDistributionUploadRelease \
  -PfirebaseDistributionGroups="yubu" \
  -PfirebaseReleaseNotes="VideoManager release"
```

You can target individual tester emails instead of a group:

```bash
./gradlew :app:assembleRelease :app:appDistributionUploadRelease \
  -PfirebaseDistributionTesters="person@example.com" \
  -PfirebaseReleaseNotes="VideoManager release"
```

For CI or service account authentication, pass a private key path or set
`GOOGLE_APPLICATION_CREDENTIALS`:

```bash
./gradlew :app:assembleRelease :app:appDistributionUploadRelease \
  -PfirebaseDistributionGroups="yubu" \
  -PfirebaseServiceCredentialsFile="/absolute/path/to/service-account.json"
```

The default tester group alias is `yubu`, so the group property can be omitted
for normal local uploads.

### Local VideoManager Upload

For this machine, use the `test1-1f100` service account key already kept in
`Downloads`. Do not copy the key into this project.

```bash
./gradlew :app:assembleRelease :app:appDistributionUploadRelease \
  -PfirebaseDistributionGroups="yubu" \
  -PfirebaseReleaseNotes="VideoManager release" \
  -PfirebaseServiceCredentialsFile="/Users/kys1207/Downloads/test1-1f100-firebase-adminsdk-fbsvc-a51d5745e4.json"
```

Known-good upload target:

```text
Firebase project: test1-1f100
Android app: com.kys.videomanager
Firebase App ID: 1:678554509202:android:647fb64535447207b6eb4b
Service account: firebase-adminsdk-fbsvc@test1-1f100.iam.gserviceaccount.com
```
