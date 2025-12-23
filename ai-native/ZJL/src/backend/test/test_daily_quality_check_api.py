"""
简单测试脚本：调用 daily_quality_check_api 的 /api/daily-quality-check 接口

使用方式:
 1) 确保服务已启动（默认 http://localhost:5001）
 2) 在本目录运行:
      python test_daily_quality_check_api.py --date 2025-01-15

可选参数:
  --url           指定服务地址，默认 http://localhost:5001
  --date          指定日期 (YYYY-MM-DD)，不填则默认昨天
  --export-excel  是否导出Excel，默认开启；使用 --no-export-excel 关闭
  --skip-dup      是否跳过重复导入，默认开启；使用 --no-skip-dup 关闭
"""

import argparse
import datetime
import json
import sys

import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Test daily_quality_check_api /api/daily-quality-check")
    parser.add_argument(
        "--url",
        default="http://localhost:5001",
        help="API base url, default: http://localhost:5001",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date string (YYYY-MM-DD). Default: yesterday",
    )
    parser.add_argument(
        "--export-excel",
        dest="export_excel",
        action="store_true",
        help="Enable Excel export (default)",
    )
    parser.add_argument(
        "--no-export-excel",
        dest="export_excel",
        action="store_false",
        help="Disable Excel export",
    )
    parser.set_defaults(export_excel=True)

    parser.add_argument(
        "--skip-dup",
        dest="skip_duplicates",
        action="store_true",
        help="Skip duplicate records (default)",
    )
    parser.add_argument(
        "--no-skip-dup",
        dest="skip_duplicates",
        action="store_false",
        help="Do not skip duplicate records",
    )
    parser.set_defaults(skip_duplicates=True)

    return parser.parse_args()


def main():
    args = parse_args()

    # Prepare date (default yesterday)
    if args.date:
        date_str = args.date
    else:
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

    payload = {
        "date": date_str,
        "export_excel": args.export_excel,
        "skip_duplicates": args.skip_duplicates,
    }

    url = args.url.rstrip("/") + "/api/daily-quality-check"

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")

    try:
        resp = requests.post(url, json=payload, timeout=120)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        sys.exit(1)

    print(f"Status: {resp.status_code}")

    # If Excel is returned, it's a file stream; otherwise JSON
    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            data = resp.json()
            print("Response JSON:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print("Response (raw text):")
            print(resp.text)
    else:
        # Save Excel file
        filename = f"test_output_{date_str}.xlsx"
        with open(filename, "wb") as f:
            f.write(resp.content)
        print(f"Excel file saved to: {filename}")


if __name__ == "__main__":
    main()

