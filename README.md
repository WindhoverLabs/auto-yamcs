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

2. Be sure to update the submodules:

```
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
python squeezer.py  --spacesystem ocpoc --yaml_path tlm_cmd_merger/src/combined.yml --output_file newdb.sqlite --verbosity 4 --remap_yaml config_remap.yaml --xtce_config_yaml ./xtce_generator/src/xtce_generator/config.yaml

```

6. Now you can open the database with sqlite browser:
```
sudo apt-get install sqlitebrowser
```
```
xdg-open newdb.sqlite
```

7. When this is all done, there will be a `ocpoc.xml` in your working directory. You can use this on a ground system such as `yamcs`.

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



Documentation updated on October 5, 2020
