[app]

# 应用名称
title = 自动阅读器

# 应用包名
package.name = autoreader

# 应用版本
package.domain = org.example
version = 1.0

# 源代码位置
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# 要包含的依赖
requirements = python3,kivy,jnius,android

# 应用权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE

# Android API级别
android.api = 28
android.minapi = 21
android.ndk = 21e

# 图标配置
#android.presplash_color = #FFFFFF
#icon.filename = %(source.dir)s/icon.png

# 构建信息
#android.ndk_path =
#android.sdk_path =
#android.ant_path =

# 额外的构建选项
android.archs = arm64-v8a, armeabi-v7a
fullscreen = 0
orientation = portrait

# 其他选项
p4a.branch = master
p4a.bootstrap = sdl2

# 服务配置
services = 
android.whitelist = 

[buildozer]
log_level = 2
warn_on_root = 1