# xtce_generator
A tool to generate xtce files from a sqlite databse. 
We follow the XTCE specifications desribed on **XTCE Verison 1.2** as per OMG document number:**formal/18-10-04**. You may find this document [here](https://www.omg.org/spec/XTCE/1.2/PDF).


## Dependencies
`six>=1.15.0`

**NOTE:** If you have issues running venv for python3.8 on Ubuntu 16, you should be able to fix it with this:
```
sudo apt install python3.8-venv python3.8-dev
```

## XTCE compliace

In the future we will strive to be 100% xtce compliant. However, given that we use `yamcs` as our ground system, if there are quirks yamcs has we will be adhering to those quirks.




### XTCE  Data Structures
Our xtce data structures are generated with `generateDS                    2.36.2`. There is a quirk with this tool where it will be name `SpaceSystem` objects to  `SpaceSystemType` after generating the python code the xtce schema. This is very easy to fix.

Go to the `export` method of your  `SpaceSystemType`.
Change it from 
```
 def export(self, outfile, level, namespaceprefix_='', namespacedef_='', name_='SpaceSystemType', pretty_print=True):
```

to
```
 def export(self, outfile, level, namespaceprefix_='', namespacedef_='', name_='SpaceSystem', pretty_print=True):
```

After renaming that parameter, you are good to go! 
**NOTE: **Beware that if you do not change this, `yamcs` will *not* run.