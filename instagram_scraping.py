from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import logging

# インスタのログイン情報
USERNAME = ''
PASSWORD = ''

# 画像の保存パス
IMAGEPATH = r''

# 検索したいユーザー名
SEARCHUSER = ''

def main():
    logging.info('処理を開始します。')
    
    # seleniumの設定
    options = webdriver.ChromeOptions()
    options.headless = False # ヘッドレスモードの場合指定
    serv = Service(ChromeDriverManager().install()) #driverの自動更新
    driver = webdriver.Chrome(service=serv, options=options)

    driver.get('https://www.instagram.com/')

    time.sleep(3)

    assert 'Instagram' in driver.title, '違うサイトにアクセスしようとしています。'

    try:
        # ログインを行う
        login(driver)
        
        # ログイン後の設定対応
        popup_notice(driver)
        
        # ユーザー検索
        user_search(driver)
        
        # 投稿数(画像数)を取得
        all_images = post_count(driver)
        if all_images is not None:
            
            # requestsでの画像の保存
            requests_img_save(all_images)

            # Pillowを使用して画像を保存する場合
            #pillow_img_save()
    except Exception as e:
        logging.error('エラー発生')
        logging.error(e)
    finally:
        logging.info('処理を終了します。')



def login(driver):
    try:
        username = driver.find_element(By.XPATH, "//input[@aria-label='電話番号、ユーザーネーム、メールアドレス']")
        username.send_keys(USERNAME)

        time.sleep(1)

        password = driver.find_element(By.XPATH, "//input[@aria-label='パスワード']")
        password.send_keys(PASSWORD)
        
        time.sleep(1)

        driver.find_element(By.XPATH, "//button[@type='submit']").submit()
        
        time.sleep(5)

    except Exception as e:
        logging.error('ユーザー名、パスワード入力時にエラーが発生しました。')
        logging.error(e)
        raise



def popup_notice(driver):
    # ログイン後のPOPUPや確認画面の対応
    try:
        driver.find_element(By.XPATH, "//button[text()='後で']").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//button[text()='後で']").click()
        time.sleep(1)
    except Exception as e:
        logging.error('ログイン後対応時にエラーが発生しました。')
        raise



def user_search(driver):
    # ユーザー検索
    try:
        search_user = driver.find_element(By.XPATH, "//input[@aria-label='検索語句']")
        # 検索したいユーザー名を設定
        search_user.send_keys(SEARCHUSER)
        time.sleep(1)
        # 検索候補の一番上をクリックする
        driver.find_element(By.XPATH, "//div[@class='_abnx _aeul']/div/a").click()
        time.sleep(5)
    except Exception as e:
        logging.error('検索時にエラーが発生しました。')
        raise



def post_count(driver):
    # ユーザー画面から投稿数を取得する
    try:
        # 投稿数を取得
        post_count = driver.find_element(By.XPATH, "//li[@class='_aa_5']/div").text
        post_count = post_count.replace('投稿', '').replace('件', '')
        post_count = int(post_count)
        
        # 1行3枚 * 4行分の12画像が表示されると次の画像群が表示されるのでpost_countが12以上で計算を行う
        if post_count > 12:
            scroll_count = int(post_count / 12) + 1
            try:
                all_images = [] # 画像保存用のリスト
                # スクロール分だけ繰り返し処理を行う
                for i in range(scroll_count):

                    # driver。page_sourceでソースコードの取得
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # HTMLからimgタグを取得
                    for image in soup.find_all('img'):
                        all_images.append(image)

                    # 画面のスクロールを行う
                    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                    time.sleep(4)
                # 引数に指定した、リスト、タプルなどをキーに辞書を作成(重複は削除される)
                all_images = list(dict.fromkeys(all_images))
                for index, image in enumerate(all_images):
                    print('画像番号: ' + str(index))
                    print("img['src']: " + image['src'], end='\n\n')
                return all_images
            except Exception as e:
                print('画面スクロール中にエラーが発生しました。')
                raise

        else:
            return None

    except Exception as e:
        logging.error('投稿数が取得出来ませんでした。')
        raise



def requests_img_save(all_images):
    # requestsでの画像の保存
    import requests
    import re
    import os
    import shutil
    try:
        for index, image in enumerate(all_images):
            filename = 'image_' + str(index) + '.jpg'
            
            # 複数のパスの要素を結合する
            image_path = os.path.join(IMAGEPATH, filename)
            image_link = image['src']
            
            # URLの形式チェック
            url_ptn = re.compile(r"^(http|https)://")
            res = url_ptn.match(image_link)
            if res:
                response = requests.get(image_link, stream=True)
                with open (image_path, 'wb') as file:
                    # ファイル形式のオブジェクトをファイルコピー
                    shutil.copyfileobj(response.raw, file)
    except Exception as e:
        logging.error(e)
        logging.error(str(index) + '番目の画像ダウンロード・保存時にエラーが発生しました。')
        logging.error('画像へのリンク:' + image_link)
        raise



def pillow_img_save(all_images):
    # Pillowを使用して画像を保存する場合
    from PIL import Image
    import io
    from urllib import request
    import ssl
    import re
    import os
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        for index, image in enumerate(all_images):
            filename = 'image_' + str(index) + '.jpg'
            
            # 複数のパスの要素を結合する
            image_path = os.path.join(IMAGEPATH, filename)
            image_link = image['src']
            
            # URLの形式チェック
            url_ptn = re.compile(r"^(http|https)://")
            res = url_ptn.match(image_link)
            if res:
                f = io.BytesIO(request.urlopen(image_link).read())
                img = Image.open(f)
                img.save(image_path)
    except Exception as e:
        logging.error(e)
        logging.error(str(index) + '番目の画像ダウンロード・保存時にエラーが発生しました。')
        logging.error('画像へのリンク:' + image_link)
        raise


if __name__ == '__main__':
    # ログの設定
    logging.basicConfig(level=logging.INFO)
    main()
