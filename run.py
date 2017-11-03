"""
実行用のファイル
"""

import urllib.request
import re
import os
import glob
import time

import tweepy
from tumblpy import Tumblpy

IMAGE_PATH = "images"


def get_tweepy():
    """ Tweepy のやつ """
    with open("twitter_config.txt", "r") as f:
        ck, cs, token, token_secret = f.read().strip().split()
    auth = tweepy.OAuthHandler(ck, cs)
    auth.set_access_token(token, token_secret)
    return tweepy.API(auth)


def delete_images():
    """ /IMAGE_PATH 以下を全部消す """
    for name in glob.glob(IMAGE_PATH + "\\*"):
        os.remove(name)


def save_images(status):
    """ 画像を /IMAGE_PATH に保存する """
    for i, entry in enumerate(status.extended_entities["media"]):
        url = entry["media_url"]
        ext = url.split(".")[3]
        filename = "{}.{}".format(i, ext)
        url += ":orig"  # 原寸大 url
        try:
            os.mkdir(IMAGE_PATH)
        except FileExistsError:
            pass

        urllib.request.urlretrieve(url, IMAGE_PATH + "\\" + filename)


def extract_titles(status):
    """
    「」『』【】内の文字列をカンマ区切りにして返す
    :return: str
    """
    text = status.full_text

    patterns = ["「.+?」", "『.+?』", "【.+?】"]
    titles = []
    for pattern in patterns:
        for word in re.findall(pattern, text):
            titles.append(word)

    # かっこを消す
    ngwords = ['「', '」', '『', '』', '【', '】']
    for ng in ngwords:
        titles = list(set(map(lambda x: x.replace(ng, ""), titles)))

    s = ",".join(titles)
    return s


def post_images(status):
    """
    画像を作品のタグと引用付きで Tumblr に Post する
    :param status: Tweepy の status オブジェクト
    :return: なし
    """
    BLOG_URL = "mangatime-kirara.tumblr.com"
    caption = status.text + "\n\n" + "Source: https://" + status.extended_entities["media"][0]["display_url"]
    tags = "manga,manga time kirara,まんがタイムきらら," + extract_titles(status)
    params = {
        "type": "photo",
        "caption": caption,
        "tags": tags,
    }

    images = []
    for i, entry in enumerate(status.extended_entities["media"]):
        url = entry["media_url"]
        ext = url.split(".")[3]
        filename = "{}.{}".format(i, ext)
        images.append(IMAGE_PATH + "\\" + filename)

    for i, image in enumerate(images):
        params["data[{}]".format(i)] = open(image, "rb")

    with open("tumblr_config.txt", "r") as f:
        ck, cs, token, token_secret = f.read().strip().split()

    t = Tumblpy(ck, cs, token, token_secret)
    t.post('post', blog_url=BLOG_URL, params=params)


def main():
    api = get_tweepy()

    # 前の更新より新しい tweet を取得する
    for status in tweepy.Cursor(api.user_timeline, id="mangatimekirara", tweet_mode="extended").items():
        # 既にふぁぼってたら終了
        if status.favorited:
            if hasattr(status, "retweeted_status"):
                continue
            else:
                break

        # ふぁぼっておく
        api.create_favorite(status.id)

        # 画像がない Tweet は無視
        if not hasattr(status, "extended_entities"):
            continue
        if "media" not in status.extended_entities:
            continue

        save_images(status)
        post_images(status)
        delete_images()
        print("Posted")

    print("Done")


if __name__ == '__main__':
    main()
