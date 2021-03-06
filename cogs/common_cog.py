# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import asyncio
import itertools
import json
import os
import random
import subprocess
import typing
from datetime import datetime, timedelta

import discord
import pandas as pd
from discord.ext import commands, tasks
from pytz import timezone


class SatsukiCom(commands.Cog, name='皐月分類外コマンド'):
    def __init__(self, bot):
        self.bot = bot
        self.SCP_JP = "http://scp-jp.wikidot.com"
        self.master_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

        self.welcome_list = [609058923353341973, 286871252784775179]
        self.BRANCHS = [
            'jp', 'en', 'ru', 'ko', 'es', 'cn', 'cs', 'fr', 'pl', 'th', 'de', 'it', 'ua', 'pt', 'uo'
        ]  # 外部に依存させたいな

        self.json_name = self.master_path + "/data/timer_dict.json"

        if not os.path.isfile(self.json_name):
            self.timer_dict = {}
            self.dump_json(self.timer_dict)

        with open(self.json_name, encoding='utf-8') as f:
            self.timer_dict = json.load(f)

        self.multi_timer.start()

    def cog_unload(self):
        self.multi_timer.cancel()

    def dump_json(self, json_data):
        with open(self.json_name, "w") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4,
                      separators=(',', ': '))

    @commands.command()
    async def url(self, ctx, call):
        call = call.strip()
        if "http" in call:
            reply = f"外部サイトを貼らないでください.{ctx.author.mention}"
        elif "/" in call[0:1]:
            reply = self.SCP_JP + call
        else:
            reply = f"{self.SCP_JP}/{call}"

        await ctx.send(reply)

    @commands.command()
    async def dice(self, ctx, num1: int, num2: typing.Optional[int] = 0):
        num_list = sorted([num1, num2])

        if any(x >= 10000 for x in num_list):
            await ctx.send("入力値が大きすぎです")
        elif any(x < 0 for x in num_list):
            await ctx.send("正の値を入力してください")

        else:
            x = random.randint(num_list[0], num_list[1])
            await ctx.send("出目は " + str(x) + " です")

    @commands.command(aliases=['lu'])
    async def last_updated(self, ctx):
        last_update_utime = os.path.getmtime(f"{self.master_path}/data/scps.csv")
        last_update_UTC_nv = datetime.fromtimestamp(int(last_update_utime))
        last_update_JST = timezone('Asia/Tokyo').localize(last_update_UTC_nv)
        await ctx.send(f"データベースの最終更新日時は{last_update_JST}です")

    @commands.command()
    async def rand(self, ctx, brt: typing.Optional[str] = 'all'):
        try:
            result = pd.read_csv(
                self.master_path +
                "/data/scps.csv",
                index_col=0)
        except FileNotFoundError as e:
            print(e)
            return

        brt = brt.lower()

        if brt in self.BRANCHS:
            result = result.query('branches in @brt')

        result = result.sample()

        result = result[0:1].values.tolist()
        result = itertools.chain(*result)
        result = list(result)

        await ctx.send(f"{result[1]}\n{self.SCP_JP}{result[0]}")

    @commands.command(aliases=['tm'])
    # @commands.has_permissions(kick_members=True)
    async def timer(self, ctx, num: typing.Optional[int] = 30):
        today = datetime.today()
        before_five = today + timedelta(minutes=num - 5)
        just_now = today + timedelta(minutes=num)

        for key in list(self.timer_dict.keys()):
            dict_time = datetime.strptime(
                self.timer_dict[key]['just'], '%Y-%m-%d %H:%M:%S')
            if today > dict_time - timedelta(minutes=5):
                self.timer_dict.pop(key, None)

        before_five = (today + timedelta(minutes=num - 5)
                       ).strftime('%Y-%m-%d %H:%M:%S')
        just_now = (today + timedelta(minutes=num)
                    ).strftime('%Y-%m-%d %H:%M:%S')
        today = today.strftime('%Y-%m-%d %H:%M:%S')

        self.timer_dict[today] = {
            "-5": f"{before_five}",
            "just": f"{just_now}",
            "author": ctx.author.mention,
            "channel": ctx.channel.id,
            "flag": 0}

        self.dump_json(self.timer_dict)

        await ctx.send(f"{ctx.author.mention} : {num}分のタイマーを開始します")

    @commands.command()
    async def help(self, ctx):
        msg = discord.Embed(
            title='本BOTの使い方を説明させていただきます.',
            description=f'よろしくお願いします.{ctx.author.mention}',
            colour=0xad1457)
        msg.add_field(
            name="/scp $scpnumber-branch$",
            value="SCP内の各国記事のURLとタイトルを返します(ex1 /scp 173 ex2 /scp 1970jp)",
            inline=False)
        msg.add_field(
            name="/search(src) $word$",
            value="ヒットした記事を表示します.",
            inline=False)
        msg.add_field(
            name="/tale $word$",
            value="taleのURL,タイトル,著者を返します(ex /tale shinjimao04)",
            inline=False)
        msg.add_field(name="/proposal(prop) $word$",
                      value="提言のURL,タイトルを返します(ex /proposal 艦橋)", inline=False)
        msg.add_field(name="/joke $word$",
                      value="jokeのURL,タイトルを返します(ex /joke ブライト)", inline=False)
        msg.add_field(
            name="/author(auth) $word$",
            value="ヒットした著者ページを表示します.",
            inline=False)
        msg.add_field(
            name="/explained(ex) $word$",
            value="ヒットしたex-scpを表示します.",
            inline=False)
        msg.add_field(
            name="/guide(gd) $word$",
            value="ヒットしたガイドページを表示します.",
            inline=False)
        msg.add_field(
            name="/draft(df)",
            value="本日の下書き予約を表示します.引数に数字を与えるとその下書き予約を表示します.",
            inline=False)
        msg.add_field(name="/url $url$",
                      value="$url$をSCPJPのアドレスに追加して返します.", inline=False)
        msg.add_field(name="/dice $int$ $int:default=0$",
                      value="サイコロを振って返します.", inline=False)
        msg.add_field(name="/last_updated(lu)",
                      value="データベースの最終更新日を表示します.", inline=False)
        msg.add_field(name="/rand",
                      value="ランダムに記事を表示します.引数で支部が指定できます.", inline=False)
        msg.add_field(name="/help", value="ヘルプです.", inline=False)
        msg.add_field(
            name="/timer $minutes:default=30$",
            value="簡易的なタイマーです.5分以上の場合、残り5分でもお知らせします.予期せぬ再起動にも安心！",
            inline=False)
        '''msg.add_field(
            name="/meeting(mt)",
            value="#scp-jp 定例会のお知らせスレッドから定例会のテーマを取得表示します.",
            inline=False)
        msg.add_field(
            name="/shuffle(sh) $num:default=2$",
            value="定例会の下書き批評回における振り分けを行います.(試験運用)",
            inline=False)'''
        msg.add_field(
            name="追記",
            value="バグ等を発見した場合は、然るべき場所にご報告ください.\n__**また、動作確認にはDMを使用することも可能です**__",
            inline=False)

        await ctx.send(embed=msg)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if any([member.guild.id == i for i in self.welcome_list]):
            channel = member.guild.system_channel
            await asyncio.sleep(3)
            embed = discord.Embed(
                title=f"{member.guild.name}へようこそ",
                colour=0x0080ff)
            embed.add_field(
                name=f"こんにちは,{member.name}.",
                value="<#548544598826287116>の確認ののち,<#464055645935501312>でアイサツをお願いします.",
                inline=True)
            embed.add_field(
                name=f"welcome {member.name}.",
                value="please check and read <#569530661350932481> and then give a reaction to this msg.",
                inline=True)
            embed.set_footer(text='読了したら何らかのリアクションをつけてください')
            try:
                await channel.send(member.mention, embed=embed)
            except BaseException:
                pass

    @tasks.loop(minutes=1.0)
    async def multi_timer(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        now_HM = now.strftime('%H:%M')
        if now_HM == '04:30':
            channel = self.bot.get_channel(638727598024687626)
            if os.name == "nt":
                await channel.send("windows上でこのコマンドは使用できません")
            elif os.name == "posix":
                subprocess.Popen(self.master_path + "/ayame.sh")
                await channel.send('菖蒲 : 更新しました')
            else:
                print("error")

        for key in self.timer_dict.keys():
            dict_time_just = datetime.strptime(
                self.timer_dict[key]['just'], '%Y-%m-%d %H:%M:%S')
            dict_time_m5 = datetime.strptime(
                self.timer_dict[key]['-5'], '%Y-%m-%d %H:%M:%S')

            if dict_time_just < now:
                mention = self.timer_dict[key]['author']
                channel = self.bot.get_channel(self.timer_dict[key]['channel'])
                await channel.send(f'時間です : {mention}')

                self.timer_dict.pop(key, None)

                self.dump_json(self.timer_dict)

            elif dict_time_m5 < now and self.timer_dict[key]['flag'] == 0:
                mention = self.timer_dict[key]['author']
                channel = self.bot.get_channel(self.timer_dict[key]['channel'])
                self.timer_dict[key]['flag'] = 1
                await channel.send(f'残り5分です : {mention}')

                self.dump_json(self.timer_dict)


def setup(bot):
    bot.add_cog(SatsukiCom(bot))
