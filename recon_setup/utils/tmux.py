def initialize_pane(pane):
    """Helper function to give zsh some time to initialize."""
    pane.send_keys("clear")
    pane.send_keys("sleep 0.2")
    pane.send_keys("clear")
