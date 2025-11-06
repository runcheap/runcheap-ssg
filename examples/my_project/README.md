# Example: My Project

This is an example of a static site that uses `runcheap-ssg` to generate the static pages.

See this example live at: [https://ssg-example.run.cheap/](https://ssg-example.run.cheap/)

How to build this example yourself:
```bash
# clone this repository
git clone https://github.com/runcheap/runcheap-ssg

# install the base library
cd runcheap-ssg/
python3 -m pip install -e .

# build and start serving this example
cd examples/my_project/
python3 manage.py runcheap_ssg_serve

# Open your browser to http://localhost:8000 to see the generated static site!
```
