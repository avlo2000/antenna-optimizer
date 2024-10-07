## Instalation
To run Docker on Windows:
- Download VcXsrv from [link](https://sourceforge.net/projects/vcxsrv/)
  - Choose "Multiple windows".
  - Check "Disable access control"
- Then run `docker-compose up --build` to run docker

### Xnec2c Quick Start Guide [(source)](https://www.xnec2c.org/)
- `git clone https://github.com/KJ7LNW/xnec2c.git`
- `cd xnec2c`
- `./autogen.sh`
- `./configure`
- `make && make install`
- `make desktop-install` # Optional: for icons and file association.
- `xnec2c`

### Other
``` bash
sudo apt install gettext
sudo apt install autopoint
sudo apt install libglib2.0-dev-bin
sudo apt install pkg-config
sudo apt-get install autoconf
sudo apt-get install libtool
sudo apt-get install libglib2.0-dev

sudo apt install make
sudo apt-get install gtk+-3.0
```

