## Instalation
### Windows:
  - Download VcXsrv from [link](https://sourceforge.net/projects/vcxsrv/)
  - Choose "Multiple windows".
  - Check "Disable access control"
  - Then run `docker-compose up --build` to run docker

### Ubuntu:
  - Grant X11 access to Docker `xhost +local:docker`
  - Run Docker `docker-compose up --build`

### Xnec2c Quick Start Guide [(source)](https://www.xnec2c.org/)
- `git clone https://github.com/KJ7LNW/xnec2c.git`
- `cd xnec2c`
- `./autogen.sh`
- `./configure`
- `make && make install`
- `make desktop-install` # Optional: for icons and file association.
- `xnec2c`
