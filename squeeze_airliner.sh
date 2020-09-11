#!/bin/bash
#This script runs juicer on airliner

cd juicer
rm build/new_db.sqlite
make
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/airliner --module "CFE" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CFS_LIB.so --module "CFS_LIB" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CF.so --module "CF" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CI.so --module "CI" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CS.so --module "CS" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/DS.so --module "DS" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/FM.so --module "FM" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/HK.so --module "HK" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/HS.so --module "HS" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/LC.so --module "LC" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/MD.so --module "MD" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/MM.so --module "MM" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/SCH.so --module "SCH" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/SC.so --module "SC" --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/TO.so --module "TO" --mode SQLITE --output build/new_db.sqlite -v4
