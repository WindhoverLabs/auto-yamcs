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
python3 squeezer.py --build_dir /home/vagrant/airliner/build/ocpoc/default --output_file newdb --verbosity 4 --yaml_path ./tlm_cmd_merger/src/combined.yml

```

3. Now you can open the database:
```
xdg-open juicer/newdb

```