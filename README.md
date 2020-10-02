# auto-yamcs
A collection of tools to auto-generate everything needed to run a ground system.

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


2. Once that builds successfully, you can run the `auto-yamcs` toolchain
```
cd auto-yamcs
python3 squeezer.py --output_file newdb --verbosity 4 --yaml_path ./tlm_cmd_merger/src/combined.yml

```

3. Now you can open the database:
```
xdg-open juicer/newdb

```

## Remapping Database Symbols
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


Documentation updated on October 2, 2020




