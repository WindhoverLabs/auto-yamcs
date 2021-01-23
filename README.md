[![Build Status](https://travis-ci.com/WindhoverLabs/auto-yamcs.svg?branch=develop)](https://travis-ci.com/WindhoverLabs/auto-yamcs)
# Table of Contents
1.  [auto-yamcs](#auto-yamcs)
2.  [Requirements](#Requirements)
3.  [How To Use It(quick and easy)](#how_to_use_it_quick)
4.  [How to Use It(fine tuning)](#how_to_use_it_tuning)
4.  [SQLite Manual Entries](#sqlite_manual_entries)
5.  [Get Up And Running Quick with YAMCS and Open MCT](#open_mct_and_yamcs)
6.  [YAML Verification](#yaml_verification)
7.  [YAML Merger](#yaml_merger)
8.  [DS Log Parser](#ds_log_parser)
9.  [Protocol Headers](#protocol_headers) 
10. [Overrides](#overrides)
11. [jinjer](#jinjer)

# auto-yamcs <a name="auto-yamcs"></a>
A collection of tools to auto-generate everything needed to run a ground system.

## Requirements <a name="Requirements"></a>

`Python>=3.6`  
`PyYAML>=5.3.1`  
`six>=1.15.0`  
`wheel>= 0.35.1`  
`pytest>=6.1.1`  
`sqlite_utils>=2.21`  
`Cerberus>=1.3.2` 


## Assumptions <a name="assumptions"></a>
- Ubuntu 16.04, 18.04 or 20.04
- The dependencies of [juicer](https://github.com/WindhoverLabs/juicer/tree/master) are satisfied.
- The "python3" command launches **python3.6** or higher.

## How To Use It(quick and easy)<a name="how_to_use_it_quick"></a>

 To make this quickstart guide work without any issues, it is highly recommended to have [airliner](https://github.com/WindhoverLabs/airliner.git) built on your system in order to use.
    Once users get through this guide, they should be able to easily use this guide as a template to run `auto-yamcs` on a non-airliner code base.
    `auto-yamcs` should work with any non-airliner code as long as the caveats stated on [juicer's](https://github.com/WindhoverLabs/juicer/tree/master) documentation
    are taken into consideration.

**NOTE**:If you want, you can start a python virtual environment such as [venv](https://docs.python.org/3/library/venv.html).
Just ensure that you run **python3.6** or higher.  


1. Install airliner and juicer Dependencies
```
apt-get install libdwarf-dev
apt-get install libelf-dev
apt-get install libsqlite3-dev
apt-get install cmake
apt-get install gcc-multilib
apt-get install g++-multilib
apt-get install maven
apt install default-jre
apt-get install openjdk-8-jdk
pip3 install pyyaml
pip3 install ruamel-yaml
pip3 install yamlpath
pip3 install cerberus
```


2. Make a `tutorial/cfs` build for airliner:
```
git clone https://github.com/WindhoverLabs/airliner.git
cd airliner
git checkout develop
make tutorial/cfs
```


3. Clone the repo and update the submodules:

```
cd ..
git clone https://github.com/WindhoverLabs/auto-yamcs.git
cd  auto-yamcs
git submodule update --init --recursive
```

After cloning `airliner` and `auto-yamcs` be sure that you have the following directory structure:

```

~/
├── airliner
│   ├── apps
│   ├── build
│   ├── config
│   ├── core
│   ├── docs
│   ├── mavlink
│   └── tools
├── auto-yamcs
│   ├── config
│   ├── juicer
│   ├── schemas
│   ├── src
│   ├── tests
│   ├── tlm_cmd_merger
│   └── xtce_generator

```

Having this directory structure will make the next steps very easy.

5. Install auto-yamcs dependencies
```
cd src
pip3 install -r ./requirements.txt
```
5. Generate XTCE  
   **NOTE**:If this is *not* your first time using `auto-yamcs`, then you may skip to the [tuning section](#how_to_use_it_tuning)
for more flexible ways of using the tool. If you are a first-time user, then *do not* skp this section.

Assuming auto-yamcs is being used alongside  `airliner` flight software, new users may use a convenience script to run
auto-yamcs:

```
./generate_xtce.sh ../../airliner/build/tutorial/cfs/target/wh_defs.yaml newdb.sqlite  ../../airliner/tools/yamcs-cfs/src/main/yamcs/mdb/cfs.xml
```

The `generate_xtce.sh` script runs auto-yamcs in `singleton` mode; in this mode there is only one YAML
file that drives the configuration of the entire workflow.

While running the script, depending on your environment, you may see the following errors and warnings:
```
...
WARNING: Cannot find data type.  Skipping.  464  errno=0 Dwarf_Error is NULL 
WARNING:squeezer:Elf file "../../airliner/build/tutorial/cfs/target/target/exe/cf/apps/VC.so" does not exist. Revise your configuration file.
ERROR:   Error in dwarf_attr(DW_AT_name).  1587  errno=114 DW_DLE_ATTR_FORM_BAD (114)
...
```
These errors and warnings, while useful for advanced usage, are __perfectly ok__.
Specially when parsing the `airliner` code base, this can take a couple of minutes. After a while, you should see
the following messages at the end:
```
INFO:xtce_generator:Writing xtce object to file...
INFO:xtce_generator:XTCE file has been written to "../../airliner/tools/yamcs-cfs/src/main/yamcs/mdb/cfs.xml"
```

As you can see auto-yamcs writes an XTCE file called `cfs.xml` to the yamcs-cfs configuration.

6. Run YAMCS  
   **NOTE**:Ensure you have the `JAVA_HOME` environment variable set on your system.
```
cd ../..
cd airliner/tools/yamcs-cfs
mvn yamcs:run
```

After running `mvn yamcs:run`, you should see the following message:
```
...
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service XtceTmRecorder
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service ParameterRecorder
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service AlarmRecorder
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service EventRecorder
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service ReplayServer
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service SystemParametersCollector
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service ProcessorCreatorService
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service CommandHistoryRecorder
17:38:22.754 yamcs-cfs [1] YamcsServerInstance Awaiting start of service ParameterArchive
17:38:22.756 _global [1] YamcsServer Yamcs started in 1642ms. Started 1 of 1 instances and 10 services
17:38:22.756 _global [1] WebPlugin Website deployed at http://MightyPenguin:8090
```

The important part here is the address follows the **http**. Go to that website on your favorite browser.

7. On a different shell/terminal, run airliner;
```
cd airliner/build/tutorial/cfs/target/target/exe
./airliner
```

Now you can view telemetry and send commands on the YAMCS web interface!

## How To Use It(fine-tuning)<a name="how_to_use_it_tuning"></a>
The following steps are meant for *advanced* users only. While this section assumes `airliner` is the flight software
being used, one can use this as a template for any other flight software that is not airliner.


5. Once airliner builds successfully and all dependencies have been installed in previous steps, you may run `auto-yamcs` in `inline` mode. In this mode you have more flexibility;
   every tool may be run separately, or may choose to not run certain tools.

An example of running all the tools in inline mode looks like the following command:
```
python3 squeezer.py inline --inline_yaml_path ../config/inline_config.yaml --remap_yaml ../config/remap.yaml  --output_file newdb.sqlite  --verbosity 3 --xtce_output_path airliner/tools/yamcs-cfs/src/main/yamcs/mdb/cfs.xml --xtce_config_yaml ../xtce_generator/config/config.yaml --override_yaml ../config/msg_def_overrides.yaml  
```
Notice how, as opposed  to `singleton` mode, there are several yaml files passed to auto-yamcs now. Most of these, except for inline_yaml_path,
are optional. Keep reading for more details on each tool such as remap and override tools.

When this is all done, there will be a `cfs.xml` in the `airliner/tools/yamcs-cfs/src/main/yamcs/mdb` directory. 
You can use this on a ground system such as `yamcs`.

6. Run YAMCS(assuming an airliner setup)
```
cd airliner/tools/yamcs-cfs
mvn yamcs:run
```


7. You can open the database with sqlite browser:
```
apt-get install sqlitebrowser
```
```
xdg-open newdb.sqlite
```


The database generated by `auto-yamcs` drives the *entire configuration* of auto-yamcs. There are several tools,
invoked explicitly in the `inline` mode above, that essentially modify the database depending on your needs. 
The following sections take a deep dive into each one of these tools. Notice that each one of them is
configurable through YAML files. Once all the tuning is done, one may use [xtce_generator](https://github.com/WindhoverLabs/xtce_generator)
to generate a xtce file that can be used for any xtce-compliant ground system such as [YAMCS](https://github.com/yamcs/yamcs).

We hope that approach provides flexibility to all users, regardless of mission needs. 


7. Remapping Database Symbols  
There might be situations where you might want to remap a database symbols to some other type. Specifically this can
be used as a workaround for when there is a symbol in the database that does not map to an intrinsic type. 
For example:

"*" = PRIMARY KEY  
"+" = FOREIGN KEY


Suppose there is a record in the `fields` table that looks like this:

| id* | symbol+ | name | byte_offset | type+ | multiplicity | little_endian | bit_size | bit_offset
| --- | --- | --- | ---| --- | --- | --- | --- | --- |
|  651 | 188 | MsgId |0 | 109 | 0 | 1 | 0 | 0

Suppose also that when we follow our `type` foreign key(109) to the symbols table:

| id* | elf+ | name | byte_size |
| ---| --- |---| --- |
| 109| 1 | CFE_SB_MsgId_t | 2|

Turns out that the symbol `CFE_SB_MsgId_t` does not map to an intrinsic type such as int32, int16, etc. We found out
this is the result of `juicer` not supporting typedef'd types intrinsic types such as `typdef int16 CFE_SB_MsgId_t`. 
For now this issue is no of high priority, but this workaround should fix issues if your code base has typedefs like the
aforementioned one. This is also extremely useful for something like the following:

This is what the `--remap_yaml` option is for.

This will remap all of the symbols specified in the config_remap.yaml on the database.

### SQLite Manual Entries <a name="sqlite_manual_entries"></a>

Some users, depending on the setup, might be in need of a mechanism to add data to the database, even after `juicer` has parsed all of the binaries. This is what the `--sql_yaml` switch is for. This flag takes a path to a yaml file as input and writes the data in the yaml to the sqlite database. The yaml file shouold look like this:

```

tables:
  symbols:
  - name: HK_PX4_SensorAccelMsg_t
    elf: ../airliner/build/squeaky_weasel/default/target/exe/airliner
    byte_size: 84
  - name: HK_PX4_SensorBaroMsg_t
    elf: ../airliner/build/squeaky_weasel/default/target/exe/airliner
    byte_size: 24

  fields:
    - symbol: HK_PX4_SensorAccelMsg_t
      name: HK_PX4_SensorAccelMsg_t_Spare1
      byte_offset: 12
      type: uint32
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorAccelMsg_t
      name: HK_PX4_SensorAccelMsg_t_Timestamp
      byte_offset: 16
      type: uint64
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorAccelMsg_t
      name: HK_PX4_SensorAccelMsg_t_ErrorCount
      byte_offset: 24
      type: uint64
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

...

    - symbol: HK_PX4_SensorAccelMsg_t
      name: HK_PX4_SensorGyroMsg_t_ZRaw
      byte_offset: 68
      type: int16
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorAccelMsg_t
      name: HK_PX4_SensorMagMsg_t_Timestamp
      byte_offset: 70
      type: uint64
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false


    - symbol: HK_PX4_SensorBaroMsg_t
      name: HK_PX4_SensorAccelMsg_t_Spare1
      byte_offset: 12
      type: uint32
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorBaroMsg_t
      name: HK_PX4_SensorBaroMsg_t_TimeStamp
      byte_offset: 16
      type: uint64
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorBaroMsg_t
      name: HK_PX4_SensorBaroMsg_t_ErrorCount
      byte_offset: 24
      type: uint32
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorBaroMsg_t
      name: HK_PX4_SensorBaroMsg_t_Pressure
      byte_offset: 28
      type: float
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

    - symbol: HK_PX4_SensorBaroMsg_t
      name: HK_PX4_SensorBaroMsg_t_Temperature
      byte_offset: 32
      type: float
      multiplicity: 0
      little_endian: 1 # 1 means true; 0 means false

  telemetry:
    - name: HK_COMBINED_PKT1_MID
      message_id: 0x0994
      symbol: HK_PX4_SensorAccelMsg_t
      module: hk

    - name: HK_COMBINED_PKT2_MID
      message_id: 0x0995
      symbol: HK_PX4_SensorBaroMsg_t
      module: hk
```

This is a short version of the `sqlite_entries.yml` file. There is also a schema of this config file in the `schemas`
directory.

## Get Up And Running Quick with YAMCS and Open MCT <a name="open_mct_and_yamcs"></a>
Once there is an xtce-compliant xml file such as `cfs.xml`, it is possible to run `yamcs` along with `Open MCT`.

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
3. Copy our `tutorial.xml` file to our yamcs database
```
cp ../auto-yamcs/tutorial.xml src/main/yamcs/mdb
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
      spec: "mdb/cfs.xml"
```

5. Run YAMCS
```
 mvn yamcs:run
```
 
If `yamcs` runs successfully, the terminal should look similar to this:
```
18:57:42.192 _global [1] XtceStaxReader Parsing XTCE file mdb/tutorial.xml
18:57:42.532 _global [1] XtceStaxReader XTCE file parsing finished, loaded: 39 parameters, 39 tm containers, 250 commands
18:57:44.964 _global [1] XtceDbFactory Serialized database saved locally
...
18:57:45.776 _global [1] YamcsServer Yamcs started in 7888ms. Started 1 of 1 instances and 10 services
18:57:45.777 _global [1] WebPlugin Website deployed at http://b7a4a04ae4b8:8090

```
 
The important part of this output is `WebPlugin Website deployed at http://b7a4a04ae4b8:8090` The `http`(might be `https` for you) part is the website where one can access the yamcs web interface. Just paste that into a browser to access yamcs.


6. Assuming an `airliner` setup, in another shell/terminal:
```
cd airliner/build/tutorial/cfs/target/exe/
./airliner
```
**NOTE**: The path to airliner will be *slightly* different if it was built for a different target other than `tutorial/cfs`.



### Open MCT

Assuming the yamcs setup was successful, now one may set up [Open MCT](https://github.com/akhenry/openmct-yamcs)  as a front-end to yamcs if desired:


1. Install Open MCT:
```
git clone https://github.com/akhenry/openmct-yamcs.git
cd openmct-yamcs
npm install
```
**NOTE:** `Open MCT` requires nodejs version **10** or higher.


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


## YAML Verification <a name="yaml_verification"></a>

Given that `auto-yamcs` uses yaml files for mall of its configuration, there needs to be a mechanism for verifying yaml
this is what the `yaml_validator is for`.

To test `yaml_validator.py`:
```
cd auto-yamcs/tests
pytest test_yaml_validator.py
```


## YAML Merger <a name="yaml_merger"></a>
Besides verifying YAML files, auto-yamcs can also merge yaml files for ad-hoc configurations:

```
pytest test_yaml_merger.py
```

Note there is a new file under the `data` folder called `merged_output.yaml`.

Notice the different between this file and the `ying.yml` and `yang.yml`:

`ying.yml`
```
...
    telemetry:
      AK8963_HK_TLM_MID:
        msgID: 0x0cc1
        struct: AK8963_HkTlm_t
...
```

`yang.yml`:

```
    telemetry:
      AK8963_HK_TLM_MID:
        msgID: 0x0cc1
        struct:
```

`merged_output.yaml`:
```
  telemetry:
    AK8963_HK_TLM_MID:
      msgID: 3265
      struct: AK8963_HkTlm_t
    AK8963_DIAG_TLM_MID:
      msgID: 3269
      struct: AK8963_DiagPacket_t
```

Notice how the telemetry element with key `AK8963_HK_TLM_MID` has the element  `AK8963_HkTlm_t` in its struct child.
This is the result of the merge.


## DS Log Parser <a name="ds_log_parser"></a>
**NOTE**: This tool is specific to `airliner`, so at the moment it should only be used when using `airliner` flight
software. In the future as log parser matures, new capability may be added to make it work with other tools. For now,
it is assumed that the user has access to telemetry logs generated by the airliner's `ds` application.

This parser is known to work for telemetry and command messages.

### To Run
```
python3 log_parser.py --structures_yaml structures.yaml --sqlite_path newdb.sqlite --input_file [PATH_TO_DS_LOG_FILE]
```

## Protocol Headers <a name="protocol_headers"></a>
`auto-yamcs` is meant to be flexible. It is meant to get a ground system running quick. Because of this, there is a way of inserting protocol headers such as `CCSDS`, `MAVLink`, etc into the database. This is useful when the database does not have an *exact* representation of the header. For example in the case of [airliner](https://github.com/WindhoverLabs/airliner), `CCSDS` is used. However, when `juicer` extracts the DWARF information, the CCSDS structures are written as an array of `char`. Which is done on purpose by the airliner developers to enforce Big Endian byte(Network Endianness) order of the ccsds headers. 

Assuming the database has been generated successfully by `auto-yamcs`, one may use `header_mod.py`:

```
python3 header_mod.py --sqlite_path newdb.sqlite --header_definitions header_mod_config.yaml
```

For an example of the structure of the config file, see `header_mod_config.yaml`.

**NOTE:** At the moment only `CCSDS` header is known to work. But any other protocol may be configured through the header_mod_config.yaml config file. Hopefully that configuration template is clear enough.

## Overrides <a name="overrides"></a>
The `msg_def_overrides.py` tool is useful for cases when a user might want to override a symbol in the database.
An example of this is strings. There are case in a code base where something might be a string but is read as a `char[]`
by `juicer`.
Another example is when enumerations are not explicit in code and are just MACROS. For these cases and any other similar
ones `msg_def_overrides.py` can be of great use.

### Usage
First define overrides in a yaml configuration file that looks like the following:
```
---
config_base: ".."
core:
  elf_files:
    - ../airliner/build/bebop2/sitl/target/exe/airliner

    cfe_es:
      short_name: cfe_es
      long_name: Core Flight Executive - Essential Services
      events: {}
      msg_def_overrides:
        - parent: CFE_ES_AppInfo_t
          member: Name
          type: string
        - parent: CFE_ES_HkPacket_Payload_t
          member: SysLogMode
          type: enumeration
          enumerations:
            OVERWRITE: 0
            DROP: 1
  ...

modules:
  ak8963:
    elf_files:
      - ../airliner/build/bebop2/sitl/target/exe/cf/apps/ak8963.so
    short_name: ak8963
    long_name: TBD
    events:
      AK8963_INIT_INF_EID:
        id: 1
        type: INFORMATION
      AK8963_CMD_NOOP_EID:
        id: 2
        type: INFORMATION
      AK8963_SUBSCRIBE_ERR_EID:
        id: 3
        type: ERROR
      AK8963_PIPE_INIT_ERR_EID:
        id: 4
        type: ERROR
      AK8963_CFGTBL_MANAGE_ERR_EID:
        id: 5
        type: ERROR
      AK8963_CFGTBL_GETADDR_ERR_EID:
        id: 6
        type: ERROR
      AK8963_RCVMSG_ERR_EID:
        id: 7
        type: ERROR
      AK8963_MSGID_ERR_EID:
        id: 8
        type: ERROR
      AK8963_CC_ERR_EID:
        id: 9
        type: ERROR
      AK8963_MSGLEN_ERR_EID:
        id: 10
        type: ERROR
      AK8963_CFGTBL_REG_ERR_EID:
        id: 11
        type: ERROR
      AK8963_CFGTBL_LOAD_ERR_EID:
        id: 12
        type: ERROR
      AK8963_UNINIT_ERR_EID:
        id: 13
        type: ERROR
      AK8963_INIT_ERR_EID:
        id: 14
        type: ERROR
      AK8963_READ_ERR_EID:
        id: 15
        type: ERROR
      AK8963_VALIDATE_ERR_EID:
        id: 16
        type: ERROR
      AK8963_CALIBRATE_INF_EID:
        id: 17
        type: INFORMATION
      AK8963_CALIBRATE_ERR_EID:
        id: 18
        type: ERROR
    msg_def_overrides:
      - parent: CFE_ES_AppInfo_t
        member: Name
        type: string
      - parent: CFE_ES_HkPacket_Payload_t
        member: SysLogMode
        type: enumeration
        enumerations:
          OVERWRITE: 0
          DROP: 1
    telemetry:
      AK8963_HK_TLM_MID:
        msgID: 0x0cc1
        struct: AK8963_HkTlm_t
      AK8963_DIAG_TLM_MID:
        msgID: 0x0cc5
        struct: AK8963_DiagPacket_t


```

Notice the new `msg_def_overrides` key in the config file; that is what `msg_def_overrides.py` will use to know
what to override.

For a full example of the config file, have a look at `auto-yamcs/tlm_cmd_merger/src/combined.yml`.


## jinjer <a name="jinjer"></a>

As you set up your ground system with YAMCS, you'll have an increasing need to displays. YAMCS Studio can be used for
such task. And for _most_ displays, creating them manually is good enough. However, there are some displays that can become
very painful to create manually as they depend of the specific build of flight software. This is where `jinjer` can help.


### Usage

```
python3 jinjer.py --template_dir [template_dir] --yaml_path [yaml_path]  --output_dir [output_dir]
```

`jinjer` uses [jinja2](https://palletsprojects.com/p/jinja/) to generate files from templates. It scans
`template_dir` for all files(including all subdirectories) and outputs a file with data from the data in yaml_path and
outputs every single file to output_dir. This can be very useful for automating display creation in  [YAMCS Studio](https://github.com/yamcs/yamcs-studio).

Documentation updated on January 22, 2021
