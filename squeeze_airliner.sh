#!/bin/bash
#This script runs juicer on airliner

cd juicer
rm build/new_db.sqlite
make
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/airliner  --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CFS_LIB.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CF.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CI.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/CS.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/DS.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/FM.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/HK.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/HS.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/LC.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/MD.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/MM.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/SCH.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/SC.so --mode SQLITE --output build/new_db.sqlite -v4
build/juicer --input /home/vagrant/airliner/build/tutorial/cfs/target/exe/cf/apps/TO.so --mode SQLITE --output build/new_db.sqlite -v4
