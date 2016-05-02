json = require "ljson"
---------------------------------------------------------------------------------------------------------------
-- Enum for SocketType & ProcType
SocketType={tcp=0,udp=1}
ProcType={worker=0,web=1,oneshot=2,portal=3}
ConfLen = {build=3,release=2,test=1,notify=1}
---------------------------------------------------------------------------------------------------------------
--- lua's copy a table
---------------------------------------------------------------------------------------------------------------
function copyTab(st)
	if type(st) ~= "table" then
		return st
	end

    local tab = {}
    for k, v in pairs(st or {}) do
        if type(v) ~= "table" then
            tab[k] = v
        else
            tab[k] = copyTab(v)
        end
    end
    return tab
end

---------------------------------------------------------------------------------------------------------------
--- input : info is port info, output is a table 
---------------------------------------------------------------------------------------------------------------
function portParser(info)
	if type(info) == "number" then
		return {["port"]=info,["type"]=SocketType["tcp"]}
	elseif type(info) == "string" then
		local pos,poe = string.find(info,":")
		local port = string.sub(info,0,pos-1)
		local portn = tonumber(port)
		local socket = string.sub(info,pos+1,-1)
		if type(portn) ~= "number" or portn < 0 or portn > 65536 then
			print_error("invalid port " .. port);
		end
		if SocketType[socket] == nil then
			print_error("invalid socket type ".. socket);
		end
		return {["port"]=port,["type"]=SocketType[socket]}
	elseif type(info) == "table" then
		for k,v in pairs(info) do
			if type(k) ~= "number" then
				print_error("unknown port ".. k)
			end
			-- print(k,v[1])
			str = string.sub(v[1],6)
			if type(str) ~= "string" or SocketType[str] == nil then
				print_error("unknown proctrol " .. str)
			end

			return {["port"]=k,["type"]=SocketType[str]}
		end
	else
		print_error("unknown port conf type " .. info)
	end
end

---------------------------------------------------------------------------------------------------------------
--- parser the type
---------------------------------------------------------------------------------------------------------------
function typeParser(info)
	
	if type(info) ~= "string" then
		print_error("invalid proc type " .. info)
	end

	if ProcType[info] == nil then
		print_error("invalid procc type" .. info)
	end

	return ProcType[info]

end

---------------------------------------------------------------------------------------------------------------
--- parser the type
---------------------------------------------------------------------------------------------------------------
function convertAllowClients(tab)

	if type(tab) == "table" then
		return tab
	elseif type(tab) == "string" then
		ans = {}
		table.insert(ans,tab)
		return ans
	end
end

---------------------------------------------------------------------------------------------------------------
--- input : yaml fileName, return the json string
---------------------------------------------------------------------------------------------------------------
function getData(fileName, repo_name, meta_version)
	tab = jsonComplete(fileName)
	tab['repo_name'] = repo_name
	tab['meta_version'] = meta_version

	return tab
end

---------------------------------------------------------------------------------------------------------------
--- check if the output table has correct content
---------------------------------------------------------------------------------------------------------------
function checkNoMoreConf(tab)
	
	for k,v in pairs({"build","release","test","notify"}) do
		if #tab[v] ~= ConfLen[v] then
			--error("Error length " .. v,0)
			print(#tab[v],v)
		end
	end
end

---------------------------------------------------------------------------------------------------------------
--- check if the output table's procs is valid
---------------------------------------------------------------------------------------------------------------

function checkProcsValid(tab)
	procs = copyTab(tab["procs"])
	for pk,pv in pairs(procs) do
		if type(pv['cpu']) ~= "number" then
			print_error("CPU number is invalid " .. pv['cpu'])
		end
		if type(pv['num_instances']) ~= "number" then
			print_error("instances number is invalid " .. pv['num_instances'])
		end
	end
end

---------------------------------------------------------------------------------------------------------------
--- check each portal has a main proc , 
---------------------------------------------------------------------------------------------------------------
function checkProtalName(tab)
	
	portalList = {}
	otherList = {}
	for pk,pv in pairs(tab['procs']) do
		if pv["type"] == ProcType["portal"] then
			print(string.sub(pv["name"],8))
			table.insert(portalList,string.sub(pv["name"],8))
		elseif pv["type"] ~= ProcType['portal'] then
			otherList[pv["name"]] = true
		end
	end


	for pk,pv in pairs(portalList) do
		if otherList[pv] == nil then
			print_error("invalid portal "..pv)
		end
	end
end

---------------------------------------------------------------------------------------------------------------
--- error function
---------------------------------------------------------------------------------------------------------------
function print_error(str)
	print("Error :" .. str)
	error(str,0)
end

---------------------------------------------------------------------------------------------------------------
--- input : yaml file name , output : json table
---------------------------------------------------------------------------------------------------------------

function jsonComplete(fileName)
	local file1=io.input(fileName)
	local str=io.read("*a")


	
	print("\n-----------------------------")
	print("Going to complete "..fileName.. " .")
	print("-----------------------------")

	--data = yaml.load(str)
	---------------------------------------------------------------------------------input is json or yaml~
	data = json.decode(str)

	---------------------------------------------------------------------------------------------------------------
	-- appname must be in yaml
	---------------------------------------------------------------------------------------------------------------
	if data["appname"] == nil then
		print_error("invalid lain conf: no appname")
	end

	---------------------------------------------------------------------------------------------------------------
	-- build must be in yaml
	---------------------------------------------------------------------------------------------------------------
	if data["build"] == nil then
		print_error("invalid lain conf: no build section in lain.yaml")
	end
	-- base must be in build
	build = data["build"]
	if build["base"] == nil then
		print_error("invalid lain conf: no base section in build")
	end
	-- build.script 
	if build["script"] == nil then
		build["script"] = ""
	end
	-- build.prepare
	if build["prepare"] == nil then
		build["prepare"] = ""
	end
	-- update data.build
	data["build"] = build


	---------------------------------------------------------------------------------------------------------------
	-- data.release
	---------------------------------------------------------------------------------------------------------------
	release = data["release"]	
	if release ~= nil then
		if release["script"] == nil then
			release["script"] = {}
		end
		if release["data_base"] == nil then
			release["data_base"] = ""
		end
		if release["copy"] == nil then
			release["copy"] = {}
		end
	else		
		release={script={},dest_base="",copy={}}
	end
	-- update release
	data["release"] = release


	---------------------------------------------------------------------------------------------------------------
	--gen procs
	---------------------------------------------------------------------------------------------------------------
	procs = {}
	default_proc = {
		name = '',
		-- type is key words in lua lang.
    		["type"] = ProcType["worker"],
    		image = '',
    		cmd = '',
    		num_instances = 1,
    		cpu = 0,
    		memory = '32m',
    		port = {["port"]=80,["type"]=SocketType["tcp"]},
    		mountpoint = {},
    		env = {},
    		volumes = {},
    		service_name = '',
    		allow_clients = '**',
    		persistent_dirs = {},
    		workdir = "",
    		user = ""
	}

	portal_default_proc = {
		name = '',
		-- type is key words in lua lang.
    		["type"] = ProcType["worker"],
    		image = '',
    		cmd = '',
    		num_instances = 1,
    		cpu = 0,
    		memory = '32m',
    		port = {["port"]=0,["type"]=SocketType["tcp"]},
    		mountpoint = {},
    		env = {},
    		volumes = {},
    		service_name = '',
    		allow_clients = '**',
    		persistent_dirs = {},
    		workdir = "",
    		user = ""
	}


	typekey = {}
	for k,v in pairs(data) do
		if k ~= "appname" and k ~= "build" and k ~= "release" and k ~= "test" and k ~= "notify" and k ~= "use_serivces" and k~="secret_files" then
			table.insert(typekey,k)
			--print(k)
		end
	end

	-- abandon list
	abandon = {}
	
	---------------------------------------------------------------------------------------------------------------
	--- update procs
	---------------------------------------------------------------------------------------------------------------
	for k,v in pairs(typekey) do

		local eachproc = copyTab(default_proc)
		local pos,poe = string.find(v,"%.")
		print(k,v,pos,poe)

		---------------------------------------------------------------------------------------------------------------
		-- if proc has no .
		---------------------------------------------------------------------------------------------------------------
		if pos == nil then
			
			local t = v
			-- judge ProcType valid or not.
			if ProcType[t] == nil then
				print_error("no such proc type "..t)
			end
			print(t)
			
			-- write value to default conf
			local localproc = data[t]
			for pk,pv in pairs(eachproc) do
				--print(pk,pv)
				if localproc[pk] ~= nil and pk ~= "port" then 
					--print(pk,localproc[pk])
					eachproc[pk] = localproc[pk]
				-- 3 types of port
				elseif pk == "port" and localproc["port"] ~= nil then
					--print(localproc[pk])
					eachproc[pk] = portParser(localproc[pk])
				end
			end

			eachproc['type'] = ProcType[t]
			eachproc['name'] = t -- ? 
			eachproc['allow_clients'] = convertAllowClients(eachproc['allow_clients'])
			table.insert(abandon,t)

			-- no duplicated proc name 
			if procs[t] ~= nil then
				print_error("duplicated proc name " .. t)
			end
			procs[t] = copyTab(eachproc)
			--print(json.encode(procs))	
		
		---------------------------------------------------------------------------------------------------------------
		-- if proc with .
		---------------------------------------------------------------------------------------------------------------
		else
			local t = string.sub(v,0,pos-1)
			local n = string.sub(v,pos+1,-1)
			print(t,n)
			---------------------------------------------------------------------------------------------------------------
			-- start with "proc"
			---------------------------------------------------------------------------------------------------------------
			if t == "proc" then
				local localproc = copyTab( data[v] )
				
				localproc["name"] = n
				
				for pk,pv in pairs(eachproc) do
					if pk == "type" and localproc[pk] ~= nil then
						eachproc[pk] = typeParser(localproc[pk])
					elseif localproc[pk] ~= nil and pk ~= "port" then 
						eachproc[pk] = localproc[pk]
					elseif pk == "port" and localproc["port"] ~= nil then
						eachproc[pk] = portParser(localproc[pk])
					end		
				end
				
				table.insert(abandon,v)
				eachproc['allow_clients'] = convertAllowClients(eachproc['allow_clients'])
			--	print(n)
			--	print(json.encode(eachproc))
				if procs[n] ~= nil then
                    print_error("duplicated proc name " .. n)
                end
				procs[n] = copyTab(eachproc)
			--	print(json.encode(procs))

			---------------------------------------------------------------------------------------------------------------
			-- not start with proc
			-- start with portal,worker,oneshot,web,service
			---------------------------------------------------------------------------------------------------------------
			elseif t == "portal" or t == "worker" or t == "oneshot" or t == "web" or t == "service" then
				local localproc = copyTab(data[v])
 				
				--print(json.encode(procs))

				localproc["name"] = n
				PreType = localproc["type"]

				if t == "service" then
					localproc["type"] = ProcType["worker"]
				else 
					localproc["type"] = ProcType[t]
				end
				
				if t == "portal" then
					eachproc = portal_default_proc
					if localproc['service_name'] == nil then
						localproc['service_name'] = string.sub(n,8)
					end
				end

				if PreType ~= nil and ProcType[PreType] ~= localproc["type"] then
					print_error("Redefine proc type and they are different.")
				end


				--print(json.encode(localproc))
                for pk,pv in pairs(eachproc) do

					if localproc[pk] ~= nil and pk ~= "port" then 
						eachproc[pk] = localproc[pk]
					elseif pk == "port" and localproc["port"] ~= nil then
						eachproc[pk] = portParser(localproc[pk])
					end
                end
 
				table.insert(abandon,v)
				--	print(n)
				-- print("eachproc",json.encode(eachproc))
				-- print("procs",json.encode(procs))

				eachproc['allow_clients'] = convertAllowClients(eachproc['allow_clients'])
                if procs[n] ~= nil then
                   print_error("duplicated proc name " .. n)
                end
				procs[n] = copyTab(eachproc)
				
				---------------------------------------------------------------------------------------------------------------
				----- start with service need check service.portal in it
				---------------------------------------------------------------------------------------------------------------
				if t == "service" then
					serviceProtal = copyTab(data[v]["portal"])
					--print(json.encode(serviceProtal))

					if data[v]["portal"] == nil then
						print_error("a service without define portal")
					end

					portalname = "portal-"..n
					
					spproc = copyTab(default_proc)

					-- print("spproc",json.encode(spproc))
					for pk,pv in pairs(spproc) do
						--print ("-------"..pk,serviceProtal[pk])
						if serviceProtal[pk] ~= nil and pk~= "port" then
							--print ("-------"..pk)
							spproc[pk] = serviceProtal[pk]
						elseif pk == "port" and serviceProtal["port"] ~= nil then
							spproc["port"] = portParser(serviceProtal[pk])
						end
					end
					----------------------------------------------------------------- default 
					if serviceProtal['service_name'] == nil then
						spproc["service_name"] = eachproc["name"]
					end

					if serviceProtal['port'] == nil then
						spproc["port"] = copyTab(eachproc["port"])
					end

                    spproc["name"] = portalname
                    spproc["type"] = ProcType["portal"]

                    spproc['allow_clients'] = convertAllowClients(spproc['allow_clients'])
					--TODO

					-- print("spproc",json.encode(spproc))
					procs[portalname] = copyTab(spproc)
				end
				---------------------------------------------------------------------------------------------------------------
				----- start with portal if service_name and port is nil then default is service's
				---------------------------------------------------------------------------------------------------------------
				if t == "portal" then
					if data[v]["service_name"] == nil then
					end
					if data[v]["port"] == nil then
						print("no service name",v)
					end
				end
			else
				print_error("unknown proc type " .. t)		
			end

		end
		print("-----------------------------")
	end

	---------------------------------------------------------------------------------------------------------------

	data["procs"] = procs
	for k,v in pairs(abandon) do
		data[v] = nil
	end
	--checkNoMoreConf(data)
	checkProcsValid(data)
	checkProtalName(data)
	ans = json.encode(data)
	print(ans)
	-- return json.decode(data)
	return data
end

--return jsonComplete(fileName)
--return jsonComplete("test_json/2.json")
return getData(fileName, repo_name, meta_version)
