import os

absPath = os.path.abspath(os.getcwd())

def createFolder(name: str):
  try:
      directory = '{}/{}'.format(absPath, name)
      if not os.path.exists(directory):
          os.makedirs(directory)
  except OSError:
      raise RuntimeError('error while create folder name {}'.format(name))