import os
import sys
import codecs
import subprocess

GIT_DESCRIPTION = "description"
LISTFILEFORMAT = u"cgit.{listname}.list"

cgitAttrMap = {
					"listname":	["cgit.listname"],
					"url": 		["cgit.url"],
					"section":	["cgit.section"],
					"owner":	["cgit.owner","gitweb.owner"],
				}

def readGitAttr(repopath, attrMap):
	os.chdir(repopath)

	answer = {}
	for attr, gitAttrList in attrMap.items():
		for gitAttr in gitAttrList:
				value = subprocess.Popen(["git","config",gitAttr], stdout=subprocess.PIPE).stdout.read().strip()
				value = unicode(value,"utf8")
				if value:
					answer[attr] = value
					break
	return answer

def readDescription(repopath):
	try:
		output = codecs.open(os.path.join(repopath,GIT_DESCRIPTION),"r","utf8").read().strip()
		output = output.split('\n',1)[0]
		return output if output else None
	except IOError:
		return None

def listRepos(path):
	childs = [ os.path.join(path,repo) for repo in os.listdir(path) ]
	return [repo for repo in childs if os.path.isdir(repo)]

def getAttrDicsForRepos(repos):
	attrDics = []
	
	for repo in repos:
		# read git attributes of $repo
		attrDic = readGitAttr(repo, cgitAttrMap)

		# discard repos without 'list'
		if not "listname" in attrDic:
			continue

		# read description
		attrDic["desc"] = readDescription(repo)

		# sanitise url
		if not "url" in attrDic:
			attrDic["url"] = os.path.basename(repo)
			if not attrDic["url"]:
				print "Internal Error: os.path.basename gave empty string on '%s'!" % repo
				sys.exit(4)

		# save path
		attrDic["path"] = repo

		# append to answer
		attrDics.append(attrDic)
	return attrDics

def writeAttrDicsToListFiles(attrDics,pathOut):
	openListFiles = {}

	for attrDic in attrDics:
		listFile = LISTFILEFORMAT.format(listname=attrDic["listname"])
	
		if not listFile in openListFiles:
			openListFiles[listFile] = codecs.open(os.path.join(pathOut,listFile),"w","utf8")
		f = openListFiles[listFile]
		f.write(u"repo.url={url}\n".format(url=attrDic["url"]))
		f.write(u"repo.path={path}\n".format(path=attrDic["path"]))
		if "section" in attrDic:
			f.write(u"repo.section={section}\n".format(section=attrDic["section"]))
		if "owner" in attrDic:
			f.write(u"repo.owner={owner}\n".format(owner=attrDic["owner"]))
		if "desc" in attrDic:
			f.write(u"repo.desc={desc}\n".format(desc=attrDic["desc"]))
		f.write('\n')

	for listFile in openListFiles:
		openListFiles[listFile].close()
		subprocess.call(["chmod","a+r",os.path.join(pathOut,listFile)])

def updateRepos(pathIn, pathOut):
	repos = listRepos(pathIn)
	attrDics = getAttrDicsForRepos(repos)
	writeAttrDicsToListFiles(attrDics,pathOut)

if __name__ == '__main__':
	if len(sys.argv) <= 2:
		print "args: path to repository, output path for list files"
		sys.exit()
	updateRepos(*sys.argv[1:3])
