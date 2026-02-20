#!/usr/bin/env python3
"""
seed_users.py  —  One-time setup: creates Firebase Auth accounts + Firestore
                   user documents for every student in the class list.

SETUP (run once):
  1. Go to Firebase Console → Project Settings → Service Accounts
  2. Click "Generate new private key" → download JSON
  3. Place it in this folder as  serviceAccountKey.json
  4. pip install firebase-admin
  5. python seed_users.py

SAFE TO RE-RUN: Already-existing users are skipped (no duplicates, no data loss).
"""

import json
import os
import sys

try:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore
except ImportError:
    sys.exit("Run: pip install firebase-admin")

# ── Students list ─────────────────────────────────────────────────────────────

STUDENTS = [
    ("24CS071", "HARI VIGNESH"),
    ("24CS072", "HARINATH S"),
    ("24CS073", "HARINI C"),
    ("24CS074", "HARINI C H"),
    ("24CS075", "HARINI K"),
    ("24CS076", "HARIPRASATH M"),
    ("24CS077", "HARIPRIYAN A"),
    ("24CS078", "HARIS BALAJEE P L"),
    ("24CS079", "HARISH G"),
    ("24CS080", "HARISH KUMAR V"),
    ("24CS081", "HARISH S"),
    ("24CS082", "HARITHA E"),
    ("24CS083", "HARSHAD R"),
    ("24CS084", "HARSHINI A"),
    ("24CS085", "HARSHITHA M P"),
    ("24CS086", "HERANYAA T P"),
    ("24CS087", "ILAMSARAVANBALAJI PA"),
    ("24CS088", "JAGATHRATCHAGAN M"),
    ("24CS089", "JAIANISH J"),
    ("24CS090", "JAISURYA S"),
    ("24CS091", "JASHWANTH J"),
    ("24CS092", "JAY PRAKASH SAH"),
    ("24CS093", "JAYASURIYA S"),
    ("24CS094", "JAYATHEERTHAN P"),
    ("24CS095", "JEFF JEROME JABEZ"),
    ("24CS096", "JENITHA M"),
    ("24CS097", "JOSHUA RUBERT R"),
    ("24CS098", "JUMAANAH BASHEETH"),
    ("24CS101", "KANHAIYA PATEL"),
    ("24CS102", "KANISH KRISHNA J P"),
    ("24CS103", "KANISH M R"),
    ("24CS104", "KANISHKA S"),
    ("24CS105", "KANWAL KISHORE"),
    ("24CS106", "KARTHIKA A"),
    ("24CS107", "KARUNESH A R"),
    ("24CS108", "KATHIRAVAN S P"),
    ("24CS109", "KATHIRVEL S"),
    ("24CS110", "KAVIN KUMAR C"),
    ("24CS111", "KAVIN PRAKASH T"),
    ("24CS112", "KAVIPRIYA P"),
    ("24CS113", "KAVYA K"),
    ("24CS114", "KAVYASRI D"),
    ("24CS115", "KEERTHI AANAND K S"),
    ("24CS116", "KHAVIYA SREE M"),
    ("24CS117", "KIRITH MALINI D S"),
    ("24CS118", "KIRITHIKA S K"),
    ("24CS119", "KOWSALYA V"),
    ("24CS120", "KRISHNA VARUN K"),
    ("24CS121", "KRISHNAN A"),
    ("24CS122", "LAVANYA R"),
    ("24CS123", "LOGAPRABHU S"),
    ("24CS124", "LOGAVARSHHNI S"),
    ("24CS125", "MADHANIKA M"),
    ("24CS126", "MADHUMITHA Y"),
    ("24CS127", "MADHUSREE M"),
    ("24CS128", "MANASA DEVI CHAPAGAIN"),
    ("24CS129", "MANISH BASNET"),
    ("24CS130", "MANISH PRAKKASH M S"),   # ← default admin
    ("24CS131", "MANOJ V"),
    ("24CS132", "MANOJKUMAR S"),
    ("24CS133", "MANSUR ANSARI"),
    ("24CS134", "MATHIYAZHINI S"),
    ("24CS135", "MATHUMITHA S"),
    ("24CS136", "MEKALA S"),
    ("24CS137", "MITHRHA Y"),
    ("24CS138", "MOHAMED ASIF S"),
    ("24CS139", "MOHAMMED SUHAIL M"),
    ("24CS140", "MOHAN KAARTHICK C"),
    ("LE01",    "NAVEEN N"),
    ("LE02",    "SUJAY S"),
    ("LE03",    "ABDHUL KAREEM L"),
]

# Roll numbers that start with admin privileges
DEFAULT_ADMINS = {"24CS130"}

EMAIL_DOMAIN = "smartclass.local"

# ── Firebase init ─────────────────────────────────────────────────────────────

KEY_FILE = os.path.join(os.path.dirname(__file__), "smart-class-da901-firebase-adminsdk-fbsvc-3b7bc6538d.json")
if not os.path.exists(KEY_FILE):
    sys.exit(
        f"\n[ERROR] serviceAccountKey.json not found at:\n  {KEY_FILE}\n\n"
        "Download it from:\n"
        "  Firebase Console → Project Settings → Service Accounts → Generate new private key\n"
    )

cred = credentials.Certificate(KEY_FILE)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ── Seed ──────────────────────────────────────────────────────────────────────

created  = 0
skipped  = 0
errors   = 0

print(f"\nSeeding {len(STUDENTS)} users into Firebase...\n")

for roll_no, display_name in STUDENTS:
    email    = f"{roll_no.lower()}@{EMAIL_DOMAIN}"
    password = roll_no               # default password = roll number
    is_admin = roll_no in DEFAULT_ADMINS

    try:
        # ── Firebase Auth ──────────────────────────────────────────────────────
        try:
            user = auth.get_user_by_email(email)
            print(f"  SKIP  {roll_no:10s}  {display_name}  (Auth user already exists)")
            skipped += 1
            uid = user.uid
        except auth.UserNotFoundError:
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
            )
            uid = user.uid
            print(f"  AUTH  {roll_no:10s}  {display_name}")

        # ── Firestore document ─────────────────────────────────────────────────
        ref = db.collection("users").document(uid)
        if not ref.get().exists:
            ref.set({
                "rollNo":            roll_no,
                "displayName":       display_name,
                "email":             email,
                "isAdmin":           is_admin,
                "isDefaultPassword": True,
                "createdAt":         firestore.SERVER_TIMESTAMP,
                "lastLoginAt":       None,
            })
            print(f"  FIRE  {roll_no:10s}  Firestore doc created  isAdmin={is_admin}")
            created += 1
        else:
            # Ensure rollNo/displayName are always up-to-date even on re-runs
            ref.update({
                "rollNo":      roll_no,
                "displayName": display_name,
            })

    except Exception as exc:
        print(f"  ERR   {roll_no:10s}  {exc}")
        errors += 1

print(f"\nDone.  created={created}  skipped={skipped}  errors={errors}\n")

if errors:
    print("[WARN] Some users failed. Check the errors above and re-run.")
else:
    print("[OK] All users are ready. You can now log in with roll_no / roll_no.")
