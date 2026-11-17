#!/usr/bin/env bash
# =====================================================================
# JinwooCrawl - SD-Card Self-Contained STB ARM Linux Installer
# Simpan folder ini di SD Card (ext4, mis. /mnt/sdcard/jinwoo-crawl):
# - backend/venv, .pw-browsers, & tmp install semuanya masuk SD Card
# - eMMC internal tetap lega
# =====================================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export TMPDIR="$ROOT_DIR/.tmp-install"
export PLAYWRIGHT_BROWSERS_PATH="$ROOT_DIR/.pw-browsers"
mkdir -p "$TMPDIR" "$PLAYWRIGHT_BROWSERS_PATH"

cleanup_tmp() {
  rm -rf "$TMPDIR" || true
}
trap cleanup_tmp EXIT

echo "=== Sisa Storage Folder Project ($ROOT_DIR) vs Root eMMC (/) ==="
df -h "$ROOT_DIR" /

# Cek kompatibilitas symlink (wajib ext4/POSIX Linux, bukan FAT32/exFAT)
if ! ln -s "$ROOT_DIR/ecosystem.config.js" "$TMPDIR/symlink_test" 2>/dev/null; then
  echo "ERROR: Filesystem di $ROOT_DIR tidak mendukung symlink Linux (kemungkinan FAT32/exFAT)."
  echo "Python venv wajib berada di partisi Linux (ext4). Format/pindahkan partisi SD Card ke ext4 terlebih dahulu."
  exit 1
fi
rm -f "$TMPDIR/symlink_test"

echo "[1/5] Membersihkan sisa cache apt/pip yang macet di eMMC..."
sudo apt-get clean || true
sudo rm -rf /var/lib/apt/lists/* /tmp/pip-* ~/.cache/pip || true

APT_FLAGS=(
  -o Acquire::Languages=none
  -o Acquire::IndexTargets::deb::Contents-deb::DefaultEnabled=false
  -o Acquire::IndexTargets::deb::Contents-udeb::DefaultEnabled=false
)

NEED_APT_PKGS=()
command -v python3 >/dev/null 2>&1 || NEED_APT_PKGS+=(python3)
python3 -m venv --help >/dev/null 2>&1 || NEED_APT_PKGS+=(python3-venv)
python3 -m pip --version >/dev/null 2>&1 || NEED_APT_PKGS+=(python3-pip)
command -v node >/dev/null 2>&1 || NEED_APT_PKGS+=(nodejs)
command -v npm >/dev/null 2>&1 || NEED_APT_PKGS+=(npm)

if [ ${#NEED_APT_PKGS[@]} -gt 0 ]; then
  echo "[2/5] Menginstall paket sistem minimum: ${NEED_APT_PKGS[*]}"
  mkdir -p "$TMPDIR/apt-lists/partial" "$TMPDIR/apt-cache/partial"
  sudo apt-get update -y "${APT_FLAGS[@]}" -o "Dir::State::lists=$TMPDIR/apt-lists"
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    -o "Dir::State::lists=$TMPDIR/apt-lists" \
    -o "Dir::Cache::archives=$TMPDIR/apt-cache" \
    "${NEED_APT_PKGS[@]}"
  sudo apt-get clean || true
else
  echo "[2/5] Python3, venv, dan Node.js sudah terpasang (skip apt-get update)."
fi

echo "[3/5] Memastikan PM2 tersedia..."
if ! command -v pm2 >/dev/null 2>&1; then
  sudo npm install -g pm2 --no-audit --no-fund
fi

echo "[4/5] Membuat Python venv & install dependencies ke SD Card ($ROOT_DIR/backend/venv)..."
if [ ! -d "$ROOT_DIR/backend/venv" ]; then
  python3 -m venv "$ROOT_DIR/backend/venv"
fi
"$ROOT_DIR/backend/venv/bin/python" -m pip install --no-cache-dir --upgrade pip
"$ROOT_DIR/backend/venv/bin/pip" install --no-cache-dir --prefer-binary -r "$ROOT_DIR/backend/requirements.txt"

echo "[5/5] Menginstall Playwright Chromium ke SD Card ($PLAYWRIGHT_BROWSERS_PATH)..."
AVAIL_SD_KB=$(df -k "$ROOT_DIR" | awk 'NR==2 {print $4}')
if [ "${AVAIL_SD_KB:-0}" -ge 600000 ]; then
  PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" "$ROOT_DIR/backend/venv/bin/playwright" install chromium || true
  mkdir -p "$TMPDIR/apt-lists/partial" "$TMPDIR/apt-cache/partial"
  if sudo apt-get update -y "${APT_FLAGS[@]}" -o "Dir::State::lists=$TMPDIR/apt-lists" >/dev/null 2>&1; then
    PW_LIBS=(libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libatspi2.0-0)
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      -o "Dir::State::lists=$TMPDIR/apt-lists" \
      -o "Dir::Cache::archives=$TMPDIR/apt-cache" \
      "${PW_LIBS[@]}" || true
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      -o "Dir::State::lists=$TMPDIR/apt-lists" \
      -o "Dir::Cache::archives=$TMPDIR/apt-cache" \
      libasound2 || sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      -o "Dir::State::lists=$TMPDIR/apt-lists" \
      -o "Dir::Cache::archives=$TMPDIR/apt-cache" \
      libasound2t64 || true
  fi
else
  echo "  PERINGATAN: Sisa ruang di $ROOT_DIR < 600MB, skip browser Playwright."
fi

unset TMPDIR TEMP TMP
mkdir -p "$ROOT_DIR/.pw-tmp"
pm2 delete jinwoocrawl-backend jinwoocrawl-frontend >/dev/null 2>&1 || true
pm2 start "$ROOT_DIR/ecosystem.config.js" --update-env
pm2 save

echo "====================================================================="
df -h "$ROOT_DIR" /
echo "Selesai! Semua venv & browser tersimpan di $ROOT_DIR"
echo "Cek status: pm2 status && pm2 logs"
echo "====================================================================="
