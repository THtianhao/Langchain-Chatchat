import os.path
import shutil
from dataclasses import asdict

from reward_any_api import *

root_path = os.path.dirname(os.path.dirname(__file__))
aime_path = os.path.join(root_path, 'knowledge_base', 'aime', 'content')

coupon_path = os.path.join(aime_path, 'coupon')
cashback_path = os.path.join(aime_path, 'cashback')
shutil.rmtree(coupon_path)
shutil.rmtree(cashback_path)

def save_json_to_file(file_name, json):
    with open(file_name, 'w') as file:
        file.write(json)


def cashback_request_n_page(num=None):
    if num is None:
        num = 999999
    page_number = 1
    has_next = True
    while has_next and page_number <= num:
        print("cashback page num = ", page_number)
        response = cashback_search(global_pub_id, global_api_key, page_number=page_number)
        json_result = json.dumps(asdict(response), indent=2)
        if not os.path.exists(cashback_path):
            os.makedirs(cashback_path)
        save_json_to_file(os.path.join(cashback_path, f'search_response_{page_number}.json'), json_result)
        page_number = response.pageNumber + 1
        has_next = response.nextPage


# 请求前n条请求
def coupon_request_n_page(num=None):
    if num is None:
        num = 999999
    page_number = 1
    total_page = 10000
    while page_number <= total_page and page_number <= num:
        print("coupon page num = ", page_number)
        response = coupon_search(global_pub_id, global_api_key, page_number=page_number)
        json_result = json.dumps(asdict(response), indent=2)
        if not os.path.exists(coupon_path):
            os.makedirs(coupon_path)
        save_json_to_file(os.path.join(coupon_path, f'search_response_{page_number}.json'), json_result)
        page_number = response.pageNumber + 1
        total_page = response.totalPages


if __name__ == "__main__":
    cashback_request_n_page()
    coupon_request_n_page()
