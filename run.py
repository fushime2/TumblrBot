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


def get_tweepy():
    """ Tweepy のやつ """
    with open("twitter_config.txt", "r") as f:
        ck, cs, token, token_secret = f.read().strip().split()
    auth = tweepy.OAuthHandler(ck, cs)
    auth.set_access_token(token, token_secret)
    return tweepy.API(auth)


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
    caption = status.full_text + "\n\n" + "Source: https://" + status.extended_entities["media"][0]["display_url"]
    tags = "manga,manga time kirara,まんがタイムきらら," + extract_titles(status)
    params = {
        "type": "photo",
        "caption": caption,
        "tags": tags,
    }

    image_urls = []
    for i, entry in enumerate(status.extended_entities["media"]):
        image_urls.append(entry["media_url"] + ":orig") # original size

    for i, url in enumerate(image_urls):
        params["data[{}]".format(i)] = urllib.request.urlopen(url)

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

        post_images(status)
        print("Posted")

    print("Done")


if __name__ == '__main__':
    main()
