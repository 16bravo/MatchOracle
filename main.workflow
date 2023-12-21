workflow "DB Initialisation" {
  on = "push"
  resolves = ["DB Initialisation"]
}

workflow "DB Update" {
  on = "workflow_run"
  resolves = ["DB Update"]
  depends-on = ["DB Initialisation"]
}

workflow "JSON Generation" {
  on = "workflow_run"
  resolves = ["JSON Generation"]
  depends-on = ["Database Update"]
}

# Jobs

job "DB Initialisation" {
  runs-on = "ubuntu-latest"
  steps = ["echo database inititalisation"]
}

job "DB Update" {
  runs-on = "ubuntu-latest"
  steps = ["echo database update"]
}

job "JSON Generation" {
  runs-on = "ubuntu-latest"
  steps = ["echo JSON generation"]
}