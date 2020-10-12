[![Build Status](https://travis-ci.com/WindhoverLabs/auto-yamcs.svg?branch=develop)](https://travis-ci.com/WindhoverLabs/auto-yamcs)

# auto-yamcs
A collection of tools to auto-generate everything needed to run a ground system.

## Requirements

`Python>=3.6`  
`PyYAML==5.3.1`  
`six==1.15.0`


## Assumptions
- Ubuntu 16.04, 18.04 or 20.04
- The dependencies of [juicer](https://github.com/WindhoverLabs/juicer/tree/master) are satisfied.

## How To Use It

1.  You *must* have [airliner](https://github.com/WindhoverLabs/airliner.git)  built on your system in order to use this at the moment. `auto-yamcs` currently only works with the `tutorial/cfs` and `ocpoc` builds.

To create a `tutorial/cfs` build for airliner:
```

cd airliner
git checkout add-documentation-to-airliner-tutorial
make tutorial/cfs
``` 
Or an `ocpoc` build:

```
cd airliner
git checkout add-documentation-to-airliner-tutorial
make ocpoc/default 
```

**NOTE**: It's possible you might get this error when building `airliner`:
```
fatal error: bits/libc-header-start.h: No such file or directory
```

You can fix that by doing this:
```
apt-get install gcc-multilib
```

2. Clone the repo and update the submodules:

```
git clone https://github.com/WindhoverLabs/auto-yamcs.git
cd  auto-yamcs
git submodule update --init
```

3. Start a virtual environment

```
python3.6 -m venv venv
```
```
. ./venv/bin/activate
```

**NOTE**: Be sure that the venv python version is **3.6** or above.

4. Install dependencies
```
pip install -r ./requirements.txt
```

5. Once that builds successfully, you can run the `auto-yamcs` toolchain
```
python squeezer.py  --spacesystem ocpoc --yaml_path tlm_cmd_merger/src/combined.yml --output_file newdb.sqlite --verbosity 4 --remap_yaml config_remap.yaml --xtce_config_yaml ./xtce_generator/src/config.yaml

```

6. Now you can open the database with sqlite browser:
```
sudo apt-get install sqlitebrowser
```
```
xdg-open newdb.sqlite
```

When this is all done, there will be a `ocpoc.xml` in your working directory. You can use this on a ground system such as `yamcs`.

7. Remapping Database Symbols  
There might be situations where you might want to remap a database symbols to some other type. Specifically this can
be used as a workaround for when there is a symbol in the database that does not map to an intrinsic type. 
For example:

"*" = PRIMARY KEY  
"+" = FOREIGN KEY


Suppose there is a record in the `fields` table that looks like this:

| id* | symbol+ | name | byte_offset | type+ | multiplicity | little_endian
| --- | --- | --- | ---| --- | --- | --- |
|  651 | 188 | MsgId |0 | 109 | 0 | 1 |

Suppose also that when we follow our `type` foreign key(109) to the symbols table:

| id* | elf+ | name | byte_size |
| ---| --- |---| --- |
| 109| 1 | CFE_SB_MsgId_t | 2|

Turns out that the symbol `CFE_SB_MsgId_t` does not map to an intrinsic type such as int32, int16, etc. We found out
this is the result of `juicer` not supporting typedef'd types intrinsic types such as `typdef int16 CFE_SB_MsgId_t`. 
For now this issue is no of high priority, but this workaround should fix issues if your code base has typedefs like the
aforementioned one.

This is what the `--remap_yaml` option is for.

This will remap all of the symbols specified in the config_remap.yaml on the database.



## Get Up And Running Quick with YAMCS and Open MCT
Once there is an xtce-compliant xml file such as `ocpoc.xml`, it is possible to run `yamcs` along with `Open MCT`.

**NOTE**: This guide assumes that `airliner` was the code base that was passed to `jucier` in the guide above, however, this can be followed as a template for any other non-airliner projects.

### YAMCS

1. Clone yamcs-cfs
```
cd ..
git clone https://github.com/WindhoverLabs/yamcs-cfs.git
```
2. 
```
cd yamcs-cfs
git checkout update-yamcs-tools
```
3. Copy our `ocpoc.xml` file to our yamcs database
```
cp ../auto-yamcs/ocpoc.xml src/main/yamcs/mdb
```
4. YAMCS will use the config file on `src/main/yamcs/etc/yamcs.yamcs-cfs.yaml ` to know which files to include in its internal database. We need to add this to the list of files

```
...
mdb:
    # Configuration of the active loaders
    # Valid loaders are: sheet, xtce or fully qualified name of the class
    - type: "xtce"
      spec: "mdb/cfs-ccsds.xml"
    - type: "xtce"
      spec: "mdb/CFE_EVS.xml"
    - type: "xtce"
      spec: "mdb/ocpoc.xml"
```

5. Run YAMCS
```
 mvn yamcs:run
```
 
If `yamcs` runs successfully, the terminal should look similar to this:
```
18:57:42.192 _global [1] XtceStaxReader Parsing XTCE file mdb/ocpoc.xml
18:57:42.532 _global [1] XtceStaxReader XTCE file parsing finished, loaded: 39 parameters, 39 tm containers, 250 commands
18:57:44.964 _global [1] XtceDbFactory Serialized database saved locally
...
18:57:45.776 _global [1] YamcsServer Yamcs started in 7888ms. Started 1 of 1 instances and 10 services
18:57:45.777 _global [1] WebPlugin Website deployed at http://b7a4a04ae4b8:8090

```
 
The important part of this output is `WebPlugin Website deployed at http://b7a4a04ae4b8:8090` The `http`(might be `https` for you) part is the website where one can access the yamcs web interface. Just paste that into a browser to access yamcs.


6. Assuming an `airliner` setup in another shell/terminal:
```
cd airliner/build/tutorial/cfs/target/exe/
./airliner
```
**NOTE**: The path to airliner will be *slightly* different if it was built for the `ocpoc` or any target other than `tutorial/cfs`.



### Open MCT

Assuming the yamcs setup was sucessful, now one may set up [Open MCT](https://github.com/akhenry/openmct-yamcs)  as a front-end to yamcs if desired:


1. Install Open MCT:
```
git clone https://github.com/akhenry/openmct-yamcs.git
cd openmct-yamcs
npm install
```
**NOTE:** `Open MCT` requires nodejs version **10** or highger.


2. Modify the Open MCT to run with the `auto-yamcs` setup. Open the `openmct-yamcs/example/index.js` file and change the `yamcsInstance` from

```
const config = {
    "yamcsDictionaryEndpoint": "http://localhost:9000/yamcs-proxy/",
    "yamcsHistoricalEndpoint": "http://localhost:9000/yamcs-proxy/",
    "yamcsRealtimeEndpoint": "ws://localhost:9000/yamcs-proxy-ws/",
    "yamcsInstance": "myproject",
    "yamcsFolder": "myproject"
};
```

to

```
const config = {
    "yamcsDictionaryEndpoint": "http://localhost:9000/yamcs-proxy/",
    "yamcsHistoricalEndpoint": "http://localhost:9000/yamcs-proxy/",
    "yamcsRealtimeEndpoint": "ws://localhost:9000/yamcs-proxy-ws/",
    "yamcsInstance": "yamcs-cfs",
    "yamcsFolder": "myproject"
};
```
Notice how the instance name is the same as our `yamcs` instance we ran above; this tells Open MCT to hook into YAMCS to fetch telemetry data.
3. Run Open MCT
```
npm start
```
The `OpenMCT` instance can be accessed on `http://localhost:9000`





Documentation updated on October 12, 2020
