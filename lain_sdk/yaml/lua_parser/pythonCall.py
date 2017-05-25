import lupa
from lupa import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)

fileName = "test_json/3.json"
repo_name = "aaa"
meta_version = "bbbb"


comd = ""
comd += "fileName = " + "'" + fileName + "'\n"
comd += "repo_name = " + "'" + repo_name + "'\n"
comd += "meta_version = " + "'" + meta_version + "'\n"

print comd

# lua.eval("dostring("+comd+")")

fo = open("jsonForPY.lua", "w+")
fo.write(comd)
fo.close()


lua.eval("dofile('jsonForPY.lua')")
a = lua.eval("dofile('jsonCompletion.lua')")

print a['appname']
print a['procs']['bar']['port']['port']
