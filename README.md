# DigiMath — Instagram avtomatik paylaşım

Hər gün avtomatik:
- **10:00 (Bakı)** — 8 sual postu (4 SAT + 4 DİM) və 8 sual Story-si
- **18:00 (Bakı)** — 8 həll Story-si

## Qovluqlar
- `content/day_XXX/` — hər günün şəkilləri və caption-ları (`manifest.json`)
- `inbox/` — yeni sual paketini (zip) bura yükləyin, sistem özü açır
- `state.json` — hansı günün paylaşıldığını yadda saxlayır (əl ilə dəyişməyin)

## Yoxlama / əl ilə işə salma
Actions → "DigiMath daily posting" → Run workflow → `check` (heç nə paylaşmır, yalnız token-i yoxlayır).

## Sual bitəndə
Material 3 gün qalanda repoda xəbərdarlıq (Issue) açılır və e-poçtunuza bildiriş gəlir.
Claude-a yazın: "növbəti həftənin suallarını hazırla" → zip-i `inbox/` qovluğuna yükləyin.
