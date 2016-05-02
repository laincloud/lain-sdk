package main

import "github.com/stevedonovan/luar"
import "fmt"


func getMapFromJson(fileName string, repo_name string, meta_version string){

    L := luar.Init()
    defer L.Close()

    luar.Register(L,"",luar.Map{
        "fileName": fileName,
        "repo_name": repo_name,
        "meta_version": meta_version,
    })

    res := L.DoFile("jsonCompletion.lua")

    if res != nil {
        fmt.Println("Error:",res)
    }

    v := luar.CopyTableToMap(L,nil,-1)   // v is the map with content

    fmt.Println("---------------------")
    fmt.Println("returned map:\n",v)
    fmt.Println("---------------------")
}


func main() {

    getMapFromJson("test_json/4.json","asdf","fdsfe")
    

}
