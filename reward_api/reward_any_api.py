import json
import requests
import argparse
from reward_api.cashback_response import CashBackResponse
from reward_api.coupon_response import CouponResponse

global_pub_id = "10427"
global_api_key = "4d0a9571ad5f0b0863f9bbcff43cda1e"
coupon_search_url = "https://api.rewardany.com/publisher/couponSearch"
cashback_url = "https://api.rewardany.com/tailored/stores-feed"


def cashback_search(pub_id, api_key, advertiser_name=None, advertiser_id=None, advertiser_country=None, page_size=500,
                    page_number=1):
    params = {
        "pubId": pub_id,
        "advertiserName": advertiser_name,
        "advertiserId": advertiser_id,
        "advertiserCountry": advertiser_country,
        "pageSize": page_size,
        "pageNumber": page_number
    }
    headers = {'Authorization': api_key}
    try:
        response = requests.get(cashback_url, params=params, headers=headers)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            # print(response_json)
            response_data = CashBackResponse(**response_json)
            # print(response_data)
            return response_data

        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发生异常: {e}")


def coupon_search(pub_id, api_key, advertiser_name=None, advertiser_id=None, advertiser_country=None, page_size=100,
                  page_number=1):
    params = {
        "pubId": pub_id,
        "advertiserName": advertiser_name,
        "advertiserId": advertiser_id,
        "advertiserCountry": advertiser_country,
        "pageSize": page_size,
        "pageNumber": page_number
    }
    headers = {'Authorization': api_key}
    try:
        response = requests.get(coupon_search_url, params=params, headers=headers)
        if response.status_code == 200:
            # print("请求成功！")
            response_json = json.loads(response.text)
            # print(response_json)
            response_data = CouponResponse(**response_json)
            # print(response_data)
            return response_data
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发生异常: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI me api")
    parser.add_argument("--apikey", help="API密钥")
    parser.add_argument("--id", help="用户ID")
    args = parser.parse_args()
    args.apikey = global_api_key
    args.id = global_pub_id

    if not args.apikey or not args.id:
        parser.print_help()
        print("请提供必要的参数：apikey 和 id")
        exit(1)

    coupon_search(args.id, args.apikey)
    cashback_search(args.id, args.apikey)
