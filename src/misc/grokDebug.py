inStr = 'BytesWritten=14504, TotalWriteTime=14, BytesRead=0, TotalReadTime=0, BlocksWritten=259, BlocksRead=0, BlocksReplicated=0, BlocksRemoved=259, BlocksVerified=0, BlockVerificationFailures=0, BlocksCached=0, BlocksUncached=0, ReadsFromLocalClient=0, ReadsFromRemoteClient=0, WritesFromLocalClient=0, WritesFromRemoteClient=259, BlocksGetLocalPathInfo=0, RemoteBytesRead=0, RemoteBytesWritten=14504, RamDiskBlocksWrite=0, RamDiskBlocksWriteFallback=0, RamDiskBytesWrite=0, RamDiskBlocksReadHits=0, RamDiskBlocksEvicted=0, RamDiskBlocksEvictedWithoutRead=0, RamDiskBlocksEvictionWindowMsNumOps=0, RamDiskBlocksEvictionWindowMsAvgTime=0.0, RamDiskBlocksLazyPersisted=0, RamDiskBlocksDeletedBeforeLazyPersisted=0, RamDiskBytesLazyPersisted=0, RamDiskBlocksLazyPersistWindowMsNumOps=0, RamDiskBlocksLazyPersistWindowMsAvgTime=0.0, FsyncCount=0, VolumeFailures=0, DatanodeNetworkErrors=0, ReadBlockOpNumOps=0, ReadBlockOpAvgTime=0.0, WriteBlockOpNumOps=259, WriteBlockOpAvgTime=22.0, BlockChecksumOpNumOps=0, BlockChecksumOpAvgTime=0.0, CopyBlockOpNumOps=0, CopyBlockOpAvgTime=0.0, ReplaceBlockOpNumOps=0, ReplaceBlockOpAvgTime=0.0, HeartbeatsNumOps=5194, HeartbeatsAvgTime=4.333333333333333, BlockReportsNumOps=2, BlockReportsAvgTime=12.0, IncrementalBlockReportsNumOps=261, IncrementalBlockReportsAvgTime=3.0, CacheReportsNumOps=1300, CacheReportsAvgTime=1.0, PacketAckRoundTripTimeNanosNumOps=222, PacketAckRoundTripTimeNanosAvgTime=6032068.0, FlushNanosNumOps=518, FlushNanosAvgTime=514220.5, FsyncNanosNumOps=0, FsyncNanosAvgTime=0.0, SendDataPacketBlockedOnNetworkNanosNumOps=0, SendDataPacketBlockedOnNetworkNanosAvgTime=0.0, SendDataPacketTransferNanosNumOps=0, SendDataPacketTransferNanosAvgTime=0.0'
test = inStr.split(', ')

newStrList = []
for e in test:
	t = e.split('=', 1)[0]
	inter = t + '=%{NUMBER:' + t +':float}'
	newStrList.append(inter)
	#print t
	# print e
	#print inter
#print newStrList
outStr = ', '.join(newStrList)
print outStr
#WriteBlockOpNumOps=%{NUMBER:WriteBlockOpNumOps:float}