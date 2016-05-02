package.path = package.path .. "yaml2json.lua"
require 'busted.runner'()
require("yaml2json")

-- Enum for SocketType & ProcType
SocketType={tcp=0,udp=1}
ProcType={worker=0,web=1,oneshot=2,portal=3}


describe("Test yaml2json converter.",function()

it("1.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/1.yaml") end)
end)

it("2.yaml", function()
  	tab = yaml2json("test/2.yaml")
  	assert.are.equals(tab['appname'],"hello")
  	assert.are.equals(tab['build']['base'],"golang")
  	assert.are.equals(tab['release']['copy'][2]['dest'],"/entry.sh")
  	assert.are.equals(tab['procs']['web']["volumes"][1],"/data")
  	assert.are.equals(tab['procs']['web']["volumes"][2],"/var/lib/mysql")
  	assert.are.equals(tab['procs']['web']['port']['port'],80)
  	assert.are.equals(tab['procs']['bar']['mountpoint'][2],"b.cn/xyz")
  	assert.are.equals(tab['procs']['foo']['memory'],"128m")
  	assert.are.equals(tab['notify']['slack'],"#hello")
end)

it("3.yaml", function()
  	tab = yaml2json("test/3.yaml")
  	assert.are.equals(tab['procs']['web']['cmd'],"")
  	--assert.are.equals(tab['procs']['web']['cmd'],"")

end)

it("4.yaml", function()
  	tab = yaml2json("test/4.yaml")
  	assert.are.equals(tab['release']['copy'][1]["dest"],"/usr/bin/hello")
  	assert.are.equals(tab['test']['script'][1],"go test")
end)

it("5.yaml", function()
  	tab = yaml2json("test/5.yaml")
  	assert.are.equals(tab['procs']['web']["env"][1],"ENV_A=enva")
  	assert.are.equals(tab['procs']['web']["volumes"][1],"/data")
end)

it("6.yaml", function()
  	tab = yaml2json("test/6.yaml")
  	assert.are.equals(tab['procs']['echo']["num_instances"],3)
  	assert.are.equals(tab['procs']['echo']["cmd"],"./echo -p 1234")
  	assert.are.equals(tab['procs']['portal-echo']["type"],ProcType['portal'])
end)

it("7.yaml", function()
  	tab = yaml2json("test/7.yaml")
  	assert.are.equals(tab['procs']['web1']["cpu"],1)
  	
end)

it("10.yaml", function()
  	
  	tab = yaml2json("test/10.yaml")
  	assert.are.equals(tab['procs']['echo']["num_instances"],5)
  	assert.are.equals(tab['procs']['portal-echo']['cmd'],"./proxy")
  	assert.are.equals(tab['procs']['portal-echo']['service_name'],"echo")

end)

it("13.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/13.yaml") end)
end)

it("14.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/14.yaml") end)
end)

it("15.yaml", function()
  	tab = yaml2json("test/15.yaml")
  	assert.are.equals(tab['procs']['web']["port"]["type"],SocketType['udp'])
end)

it("16.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/16.yaml") end)
end)

it("17.yaml", function()
  	tab = yaml2json("test/17.yaml")
  	assert.are.equals(tab['procs']['asdf']["type"],ProcType['web'])
  	assert.are.equals(tab['procs']['asdf']['cmd'],"hello")
  	
end)

it("19.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/19.yaml") end)
end)

it("20.yaml", function()
  	tab = yaml2json("test/20.yaml")
  	assert.are.equals(tab["secret_files"][1],"secrets/root_password")
  	assert.are.equals(tab["procs"]["mysqld"]['persistent_dirs'][1],"/var/lib/mysql/")
  	
end)

it("21.yaml", function()
  	tab = yaml2json("test/21.yaml")
  	assert.are.equals(tab["procs"]["portal-echo"]['allow_clients'][1],"hehe")
  	assert.are.equals(tab["procs"]["echo"]['allow_clients'][1],"**")
  	
end)

it("22.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/22.yaml") end)
end)

it("23.yaml", function()
  	tab = yaml2json("test/23.yaml")
  	--assert.are.equals(tab["procs"]["portal-echo"]['allow_clients'][1],"hehe")
  	--assert.are.equals(tab["procs"]["echo"]['allow_clients'][1],"**")
  	    
        assert.are.equals(tab['procs']['echo']['port']['port'],1234)
        assert.are.equals(tab['procs']['portal-echo']['service_name'],"echo")
end)

it("24.yaml", function()
  assert.has_error(function() 
  	tab = yaml2json("test/24.yaml") end)
end)

end)